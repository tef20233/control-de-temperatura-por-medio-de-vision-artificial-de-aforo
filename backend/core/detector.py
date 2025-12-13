from ultralytics import YOLO
import numpy as np
import os
import time
import torch
from scipy.stats import mode

class YOLOEnsembleDetector:
    """
    Detector que carga dinámicamente 1-4 modelos YOLO disponibles
    y hace ensemble/voting para mejorar precisión

    OPTIMIZADO PARA 30+ FPS:
    - Auto-detección de GPU
    - FP16 en GPUs NVIDIA
    - Resolución optimizada (416px)
    - NMS optimizado
    """

    def __init__(self, models_dir=None):
        if models_dir is None:
            # Resolver ruta absoluta basada en la ubicación de este archivo
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            models_dir = os.path.join(base_dir, 'models')
        
        self.models_dir = models_dir
        self.models = {}
        self.model_names = ['yolo11s']  # SOLO yolo11s.pt
        self._strategy_logged = False  # Para no repetir el log

        # Detectar dispositivo (GPU/CPU) y capacidades
        self.device = self._detect_best_device()
        self.use_half = self._can_use_fp16()
        
        # OPTIMIZACIÓN GPU: Configurar CUDA para máximo rendimiento
        if 'cuda' in self.device:
            torch.backends.cudnn.benchmark = True  # Auto-tune kernels
            torch.backends.cuda.matmul.allow_tf32 = True  # Usar TF32 en 1050 Ti
            torch.cuda.set_device(0)  # Forzar GPU 0
            # Limpiar cache inicial
            torch.cuda.empty_cache()
            print("⚡ CUDA optimizado: benchmark=True, TF32=True")
        
        # Métricas conocidas de cada modelo (hardcoded from training)
        self.model_metrics = {
            'yolov11n': {'precision': 0.910, 'recall': 0.855, 'mAP50': 0.895}
        }
        
        self.load_available_models()
        self._warmup_gpu()  # IMPORTANTE: Precalentar GPU

    def _detect_best_device(self):
        """Detectar el mejor dispositivo disponible (GPU/CPU)"""
        if torch.cuda.is_available():
            device = 'cuda:0'
            gpu_name = torch.cuda.get_device_name(0)
            print(f"🚀 GPU detectada: {gpu_name}")
            print(f"   VRAM disponible: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            device = 'mps'  # Apple Silicon
            print(f"🍎 Apple Silicon (MPS) detectado")
        else:
            device = 'cpu'
            print(f"💻 Usando CPU (considera usar GPU para 3-5x más velocidad)")

        return device

    def _can_use_fp16(self):
        """Verificar si el dispositivo soporta FP16 (half precision)"""
        if self.device == 'cpu':
            return False  # CPU no soporta FP16 eficientemente

        if 'cuda' in self.device:
            # GTX 1050 Ti (compute 6.1) no soporta FP16 eficientemente
            # Solo >= 7.0 (Volta/Turing/Ampere) tiene Tensor Cores
            capability = torch.cuda.get_device_capability(0)
            if capability[0] >= 7:
                print(f"⚡ FP16 (half precision) ACTIVADO → 2x más rápido")
                return True
            else:
                print(f"💡 GPU GTX/RTX (compute {capability[0]}.{capability[1]}) - usando FP32 optimizado")
                return False

        # Apple MPS no soporta FP16 aún
        return False

    def load_available_models(self):
        """Busca y carga modelos .pt disponibles"""
        print("\n📦 Buscando modelos YOLO...")
        
        for model_name in self.model_names:
            model_path = os.path.join(self.models_dir, f'{model_name}.pt')
            
            if os.path.exists(model_path):
                try:
                    model = YOLO(model_path)
                    self.models[model_name] = model
                    print(f"✅ {model_name} cargado - {model_path}")
                except Exception as e:
                    print(f"❌ Error cargando {model_name}: {e}")
            else:
                print(f"⚠️ {model_name} no encontrado - {model_path}")
        
        if len(self.models) == 0:
            raise Exception("❌ No se encontró ningún modelo YOLO válido")
        
        print(f"\n🎯 {len(self.models)}/{len(self.model_names)} modelos cargados\n")
    
    def _warmup_gpu(self):
        """Precalentar GPU con inferencias dummy para estabilizar FPS"""
        if 'cuda' not in self.device:
            return
        
        print("🔥 Precalentando GPU...")
        # Crear frame dummy con resolución objetivo
        dummy_frame = np.zeros((360, 480, 3), dtype=np.uint8)
        
        # Ejecutar 10 inferencias para calentar GPU
        for model_name, model in self.models.items():
            for i in range(10):
                _ = model(
                    dummy_frame,
                    conf=0.35,
                    iou=0.45,
                    imgsz=256,
                    verbose=False,
                    device=self.device,
                    half=self.use_half
                )
        
        # Sincronizar GPU
        if 'cuda' in self.device:
            torch.cuda.synchronize()
        
        print("✅ GPU precalentada - FPS estabilizados\n")
    
    def detect(self, frame, confidence=0.35, strategy='union', imgsz=192, iou=0.5, max_det=10):
        """
        Ejecuta inferencia con TODOS los modelos disponibles
        
        Args:
            frame: Frame de OpenCV (numpy array)
            confidence: Umbral de confianza (0-1) - BAJADO A 0.35 para mejor recall
            strategy: Estrategia de ensemble ('average', 'majority', 'best', 'union')
        
        Returns:
            {
                'count': int,              # Conteo final (votado/promediado)
                'detections': List[Dict],  # Bounding boxes finales
                'models_used': List[str],  # Modelos que hicieron predicción
                'individual_counts': Dict, # Conteo por modelo
                'fps': float,
                'inference_time': float
            }
        """
        start_time = time.time()
        
        frame_h, frame_w = frame.shape[:2]
        min_area_ratio = 0.0025
        max_area_ratio = 0.6
        min_aspect_ratio = 0.5
        
        predictions = []
        individual_counts = {}
        
        # Si strategy='best', solo usar el modelo más rápido y preciso (yolo11s)
        if strategy == 'best':
            # Prioridad: yolo11s > yolov11s > yolov11n
            target_model = None
            for m in ['yolo11s', 'yolov11s', 'yolov11n']:
                if self.models.get(m) is not None:
                    target_model = m
                    break
            
            if target_model:
                models_to_use = {target_model: self.models[target_model]}
                if not self._strategy_logged:
                    print(f"⚡ Usando modelo: {target_model} (modo best/rápido)")
                    self._strategy_logged = True
            else:
                # Fallback
                first_key = list(self.models.keys())[0]
                models_to_use = {first_key: self.models[first_key]}
                if not self._strategy_logged:
                    print(f"⚡ Usando modelo: {first_key} (fallback)")
                    self._strategy_logged = True
        else:
            models_to_use = self.models
            if not self._strategy_logged:
                print(f"⚡ Usando {len(models_to_use)} modelos: {list(models_to_use.keys())}")
                self._strategy_logged = True
        
        # Ejecutar inferencia en cada modelo optimizado para velocidad
        for model_name, model in models_to_use.items():
            try:
                # ULTRA-OPTIMIZACIÓN para stream fluido
                results = model(
                    frame,
                    conf=confidence,
                    iou=iou,  # NMS ultra-agresivo
                    imgsz=imgsz,  # ULTRA-RÁPIDO: 192px = stream fluido
                    verbose=False,
                    max_det=max_det,  # Máximo 10 personas
                    half=self.use_half,
                    device=self.device,
                    # Máxima velocidad para stream
                    agnostic_nms=False,
                    classes=[0],  # SOLO personas
                    stream=False,
                    augment=False,
                    retina_masks=False,
                )
                boxes = results[0].boxes
                
                detections = []
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    
                    w_box = x2 - x1
                    h_box = y2 - y1
                    if w_box <= 0 or h_box <= 0:
                        continue
                    area = w_box * h_box
                    area_ratio = area / float(frame_w * frame_h)
                    aspect_ratio = h_box / float(w_box)
                    if area_ratio < min_area_ratio or area_ratio > max_area_ratio:
                        continue
                    if aspect_ratio < min_aspect_ratio:
                        continue
                    
                    if cls == 0:
                        detections.append({
                            'bbox': [x1, y1, x2, y2],
                            'confidence': conf,
                            'class': 'person',
                            'model': model_name
                        })
                
                count = len(detections)
                individual_counts[model_name] = count
                
                predictions.append({
                    'model': model_name,
                    'count': count,
                    'detections': detections
                })
                
            except Exception as e:
                print(f"⚠️ Error en {model_name}: {e}")
        
        # Aplicar estrategia de ensemble
        final_count, final_detections = self.ensemble_vote(predictions, strategy, iou)
        
        inference_time = time.time() - start_time
        fps = 1.0 / inference_time if inference_time > 0 else 0
        
        return {
            'count': final_count,
            'detections': final_detections,
            'models_used': list(models_to_use.keys()),  # Solo los modelos realmente usados
            'individual_counts': individual_counts,
            'inference_time': inference_time,
            'fps': fps
        }
    
    def ensemble_vote(self, predictions, strategy, iou):
        """
        Combina predicciones de múltiples modelos
        
        Estrategias:
        - PROMEDIO: count = mean([count_1, count_2, ..., count_n])
        - MAYORÍA: count = mode([count_1, count_2, ..., count_n])
        - MEJOR: count = prediction del modelo con mayor mAP
        - UNIÓN: merge todas las detecciones + NMS global
        """
        if len(predictions) == 0:
            return 0, []
        
        if len(predictions) == 1:
            return predictions[0]['count'], predictions[0]['detections']
        
        counts = [p['count'] for p in predictions]
        
        if strategy == 'average':
            # Promedio redondeado
            final_count = int(round(np.mean(counts)))
            # Usar detecciones del modelo con conteo más cercano al promedio
            closest_pred = min(predictions, key=lambda p: abs(p['count'] - final_count))
            final_detections = closest_pred['detections']
        
        elif strategy == 'majority':
            # Moda (más frecuente)
            final_count = int(mode(counts, keepdims=False).mode)
            # Usar detecciones del primer modelo con ese conteo
            final_detections = []
            for pred in predictions:
                if pred['count'] == final_count:
                    final_detections = pred['detections']
                    break
        
        elif strategy == 'best':
            # Usar predicción del modelo con mayor mAP conocido
            priority = {'yolov8l': 4, 'yolov8m': 3, 'yolov8s': 2, 'yolov8n': 1}
            best_pred = max(predictions, key=lambda p: priority.get(p['model'], 0))
            final_count = best_pred['count']
            final_detections = best_pred['detections']
        
        elif strategy == 'union':
            # Unión de todas las detecciones + NMS global (MEJOR PARA CONTEO)
            all_detections = []
            for pred in predictions:
                all_detections.extend(pred['detections'])
            
            # OPTIMIZADO: NMS global con threshold 0.5 (menos comparaciones)
            final_detections = self.apply_nms(all_detections, iou_threshold=iou)
            final_count = len(final_detections)
        
        else:
            # Default: average
            final_count = int(round(np.mean(counts)))
            closest_pred = min(predictions, key=lambda p: abs(p['count'] - final_count))
            final_detections = closest_pred['detections']
        
        return final_count, final_detections
    
    def apply_nms(self, detections, iou_threshold=0.5):
        """Non-Maximum Suppression para eliminar detecciones duplicadas

        OPTIMIZADO: IoU threshold 0.5 (antes 0.4)
        - Menos comparaciones = más rápido
        - Aún mantiene detecciones distintas
        """
        if len(detections) == 0:
            return []
        
        # Convertir a arrays numpy
        boxes = np.array([d['bbox'] for d in detections])
        scores = np.array([d['confidence'] for d in detections])
        
        # Calcular áreas
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)
        
        # Ordenar por confianza
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            # Calcular IoU con el resto
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            
            intersection = w * h
            iou = intersection / (areas[i] + areas[order[1:]] - intersection)
            
            # Mantener solo los que tienen IoU < threshold
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        return [detections[i] for i in keep]
    
    def get_loaded_models(self):
        """Retorna lista de modelos cargados"""
        return list(self.models.keys())
    
    def get_missing_models(self):
        """Retorna lista de modelos no encontrados"""
        return [name for name in self.model_names if name not in self.models]
    
    def get_models_info(self):
        """Retorna info detallada de cada modelo"""
        info = {'models': {}}
        
        for model_name in self.model_names:
            if model_name in self.models:
                metrics = self.model_metrics.get(model_name, {})
                info['models'][model_name] = {
                    'loaded': True,
                    'path': os.path.join(self.models_dir, f'{model_name}.pt'),
                    'precision': metrics.get('precision', 'N/A'),
                    'recall': metrics.get('recall', 'N/A'),
                    'mAP50': metrics.get('mAP50', 'N/A')
                }
            else:
                info['models'][model_name] = {
                    'loaded': False,
                    'message': 'Model file not found'
                }
        
        return info
