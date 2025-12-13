import React from 'react';
import { View, StyleSheet, StatusBar } from 'react-native';
import HomeScreenSimple from './src/screens/HomeScreenSimple';

export default function App() {
  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#3b82f6" />
      <HomeScreenSimple />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});
