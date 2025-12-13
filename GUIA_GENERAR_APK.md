# 📱 Guía para Generar el APK (Android)

Esta guía te permitirá generar el archivo instalable `.apk` de la aplicación móvil para probarlo en tu celular.

## 1. Prerrequisitos
Asegúrate de tener instalado Node.js y npm.

1.  Instala la herramienta de línea de comandos de EAS (Expo Application Services):
    ```powershell
    npm install -g eas-cli
    ```

2.  Inicia sesión en tu cuenta de Expo (si no tienes una, regístrate gratis en [expo.dev](https://expo.dev)):
    ```powershell
    eas login
    ```

## 2. Configuración de Conexión (¡IMPORTANTE!)
Para que la App funcione en tu celular, debe poder conectarse a tu PC.

1.  He actualizado automáticamente el archivo `frontend/src/utils/constants.js` con tu IP actual: **`192.168.20.45`**.
2.  **Asegúrate de que tu celular y tu PC estén conectados a la misma red Wi-Fi.**
3.  Si tu IP cambia (por ejemplo, si reinicias el router), deberás actualizarla manualmente en ese archivo antes de generar un nuevo APK.

## 3. Generar el APK
Ejecuta los siguientes comandos desde la carpeta `frontend`:

1.  Ve a la carpeta frontend:
    ```powershell
    cd frontend
    ```

2.  Ejecuta el comando de construcción para Android (perfil 'preview' para generar APK):
    ```powershell
    eas build -p android --profile preview
    ```

3.  **Sigue las instrucciones en pantalla**:
    *   Si te pregunta si quieres generar un Keystore, di que **Sí** (Y).
    *   Espera a que termine el proceso (se hace en la nube).
    *   Al finalizar, te dará un **Link de descarga** del `.apk`.

## 4. Instalar en el Celular
1.  Descarga el archivo `.apk` desde el link proporcionado.
2.  Pásalo a tu celular (por USB, WhatsApp, Drive, etc.).
3.  Instálalo (debes permitir "Instalar aplicaciones desconocidas").
4.  Abre la App. Debería conectarse automáticamente a tu backend si está corriendo en el PC.

## 💡 Solución de Problemas de Conexión
Si la App se abre pero no muestra datos:
*   Verifica que el backend esté corriendo (`start_full_system.ps1` o `run_camera.ps1`).
*   Verifica el Firewall de Windows: Asegúrate de que Python tenga permiso para recibir conexiones en redes privadas/públicas.
*   Verifica que la IP en `frontend/src/utils/constants.js` sea la correcta (usa `ipconfig` en terminal para ver tu IP actual).
