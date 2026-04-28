import { useState } from 'react';
import { View, Text, Image, ScrollView, TouchableOpacity, StyleSheet, Linking } from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import * as Speech from 'expo-speech';

const TOPIC_COLORS: Record<string, string> = {
  Science: '#4ECDC4', Space: '#9B5DE5', Animals: '#00B4D8',
  Sports: '#FF6B35', Technology: '#06D6A0', Weather: '#118AB2',
  Arts: '#EF476F', Environment: '#57CC99',
};

export default function ArticleScreen() {
  const { title, summary, funFact, url, image, topic, date } = useLocalSearchParams<{
    title: string; summary: string; funFact: string;
    url: string; image: string; topic: string; date: string;
  }>();
  const router = useRouter();
  const color = TOPIC_COLORS[topic] || '#888';
  const [isSpeaking, setIsSpeaking] = useState(false);

  function handleSpeak() {
    if (isSpeaking) {
      Speech.stop();
      setIsSpeaking(false);
      return;
    }

    const textToRead = `${title}. ${summary}. ${funFact ? `Did you know? ${funFact}` : ''}`;

    Speech.speak(textToRead, {
      language: 'en',
      pitch: 1.1,    // slightly higher pitch — friendlier for kids
      rate: 0.85,    // slightly slower — easier for kids to follow
      onDone: () => setIsSpeaking(false),
      onStopped: () => setIsSpeaking(false),
      onError: () => setIsSpeaking(false),
    });
    setIsSpeaking(true);
  }

  return (
    <ScrollView style={styles.container}>
      {image ? (
        <Image source={{ uri: image }} style={styles.image} />
      ) : (
        <View style={[styles.imagePlaceholder, { backgroundColor: color + '22' }]}>
          <Text style={{ fontSize: 72 }}>📰</Text>
        </View>
      )}

      <View style={styles.body}>
        <View style={styles.meta}>
          <View style={[styles.topicTag, { backgroundColor: color }]}>
            <Text style={styles.topicTagText}>{topic}</Text>
          </View>
          <Text style={styles.date}>{date}</Text>
        </View>

        <Text style={styles.title}>{title}</Text>

        {/* Voice button */}
        <TouchableOpacity
          style={[styles.voiceBtn, isSpeaking && styles.voiceBtnActive]}
          onPress={handleSpeak}>
          <Text style={styles.voiceBtnText}>
            {isSpeaking ? '⏹️ Stop Reading' : '🔊 Read Aloud'}
          </Text>
        </TouchableOpacity>

        <Text style={styles.summary}>{summary}</Text>

        {funFact ? (
          <View style={styles.funFact}>
            <Text style={styles.funFactLabel}>💡 Did you know?</Text>
            <Text style={styles.funFactText}>{funFact}</Text>
          </View>
        ) : null}

        {url ? (
          <TouchableOpacity style={styles.readBtn} onPress={() => Linking.openURL(url)}>
            <Text style={styles.readBtnText}>Read original article →</Text>
          </TouchableOpacity>
        ) : null}

        <TouchableOpacity style={styles.backBtn} onPress={() => {
          Speech.stop();
          router.back();
        }}>
          <Text style={styles.backBtnText}>← Back to news</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF9F0' },
  image: { width: '100%', height: 240 },
  imagePlaceholder: { width: '100%', height: 240, justifyContent: 'center', alignItems: 'center' },
  body: { padding: 20 },
  meta: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  topicTag: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 99 },
  topicTagText: { color: 'white', fontSize: 12, fontWeight: '700', textTransform: 'uppercase' },
  date: { fontSize: 13, color: '#888' },
  title: { fontSize: 24, fontWeight: '800', color: '#1A1208', lineHeight: 32, marginBottom: 16 },
  voiceBtn: { backgroundColor: '#1A1208', padding: 14, borderRadius: 12, alignItems: 'center', marginBottom: 20, flexDirection: 'row', justifyContent: 'center' },
  voiceBtnActive: { backgroundColor: '#FF6B35' },
  voiceBtnText: { color: 'white', fontSize: 16, fontWeight: '700' },
  summary: { fontSize: 16, color: '#444', lineHeight: 26, marginBottom: 20 },
  funFact: { backgroundColor: '#FFFBF0', borderWidth: 1, borderColor: '#FFE66D', borderRadius: 12, padding: 16, marginBottom: 24 },
  funFactLabel: { fontSize: 14, fontWeight: '700', color: '#5A4000', marginBottom: 6 },
  funFactText: { fontSize: 14, color: '#7A5C00', lineHeight: 22 },
  readBtn: { backgroundColor: '#FF6B35', padding: 16, borderRadius: 12, alignItems: 'center', marginBottom: 12 },
  readBtnText: { color: 'white', fontSize: 16, fontWeight: '700' },
  backBtn: { padding: 16, alignItems: 'center' },
  backBtnText: { color: '#888', fontSize: 14 },
});
