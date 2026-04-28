import { View, Text, TouchableOpacity, StyleSheet, Linking } from 'react-native';

export default function SubscribeScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.emoji}>🌟</Text>
      <Text style={styles.title}>Get The Daily Whiz</Text>
      <Text style={styles.subtitle}>Subscribe to get personalized kids news delivered to your inbox every day</Text>

      <TouchableOpacity
        style={styles.btn}
        onPress={() => Linking.openURL('https://safekidsnews.com/index.html')}>
        <Text style={styles.btnText}>Subscribe Now →</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.btnSecondary}
        onPress={() => Linking.openURL('https://safekidsnews.com/app.html')}>
        <Text style={styles.btnSecondaryText}>Browse on Web →</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF9F0', justifyContent: 'center', alignItems: 'center', padding: 32 },
  emoji: { fontSize: 64, marginBottom: 16 },
  title: { fontSize: 28, fontWeight: '800', color: '#1A1208', textAlign: 'center', marginBottom: 12 },
  subtitle: { fontSize: 16, color: '#666', textAlign: 'center', lineHeight: 24, marginBottom: 32 },
  btn: { backgroundColor: '#FF6B35', padding: 16, borderRadius: 12, width: '100%', alignItems: 'center', marginBottom: 12 },
  btnText: { color: 'white', fontSize: 16, fontWeight: '700' },
  btnSecondary: { backgroundColor: 'white', padding: 16, borderRadius: 12, width: '100%', alignItems: 'center', borderWidth: 1, borderColor: '#EDE5D8' },
  btnSecondaryText: { color: '#1A1208', fontSize: 16, fontWeight: '600' },
});