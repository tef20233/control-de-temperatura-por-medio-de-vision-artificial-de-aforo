import React, { useState } from 'react';
import { View, StyleSheet, StatusBar } from 'react-native';
import HomeScreenSimple from './src/screens/HomeScreenSimple';
import WelcomeScreen from './src/screens/WelcomeScreen';

export default function App() {
  const [showDashboard, setShowDashboard] = useState(false);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#080C14" />
      {showDashboard ? (
        <HomeScreenSimple />
      ) : (
        <WelcomeScreen onEnter={() => setShowDashboard(true)} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#080C14',
  },
});

