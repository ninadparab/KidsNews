import { useState } from 'react';
import {
  View, Text, Image, ScrollView, TouchableOpacity,
  StyleSheet, Linking, Share, Platform,
} from 'react-native';
import { useLocalSearchParams, useRouter } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as Speech from 'expo-speech';
import { Ionicons } from '@expo/vector-icons';

const TOPIC_COLORS: Record<string, string> = {
  Science: '#4ECDC4', Space: '#9B5DE5', Animals: '#00B4D8',
  Sports: '#FF6B35', Technology: '#06D6A0', Weather: '#118AB2',
  Arts: '#EF476F', Environment: '#57CC99',
};

const TOPIC_EMOJIS: Record<string, string> = {
  Science: '🔬', Space: '🚀', Animals: '🦁', Sports: '⚽',
  Technology: '💻', Weather: '🌤️', Arts: '🎨', Environment: '🌿',
};

function getReadTime(text: string): string {
  if (!text) return '1 min read';
  const words = text.trim().split(/\s+/).length;
  return `${Math.max(1, Math.ceil(words / 150))} min read`;
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr + 'T12:00:00').toLocaleDateString('en-US', {
      month: 'long', day: 'numeric', year: 'numeric',
    });
  } catch { return dateStr; }
}

export default function ArticleScreen() {
  const { title, summary, funFact, url, image, topic, date, source } = useLocalSearchParams<{
    title: string; summary: string; funFact: string;
    url: string; image: string; topic: string; date: string; source: string;
  }>();
  const router = useRouter();
  const insets = useSafeAreaInsets();
  const color = TOPIC_COLORS[topic] || '#888';
  const emoji = TOPIC_EMOJIS[topic] || '📰';
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [progress, setProgress] = useState(0);
  const readTime = getReadTime(summary);

  function handleSpeak() {
    if (isSpeaking) {
      Speech.stop();
      setIsSpeaking(false);
      return;
    }
    const textToRead = `${title}. ${summary}. ${funFact ? `Did you know? ${funFact}` : ''}`;
    Speech.speak(textToRead, {
      language: 'en',
      pitch: 1.1,
      rate: 0.85,
      onDone: () => setIsSpeaking(false),
      onStopped: () => setIsSpeaking(false),
      onError: () => setIsSpeaking(false),
    });
    setIsSpeaking(true);
  }

  async function handleShare() {
    try {
      await Share.share({
        message: `${title}\n\n${summary}\n\nFrom The Daily Whiz — safe news for kids`,
        ...(Platform.OS === 'ios' && url ? { url } : {}),
      });
    } catch {}
  }

  function handleBack() {
    Speech.stop();
    router.back();
  }

  return (
    <View style={[styles.container, { paddingTop: insets.top }]}>

      {/* Custom header */}
      <View style={styles.header}>
        <TouchableOpacity style={styles.headerBtn} onPress={handleBack} activeOpacity={0.7}>
          <Ionicons name="arrow-back" size={22} color="#1A1208" />
        </TouchableOpacity>
        <Text style={styles.headerTitle} numberOfLines={1}>{topic}</Text>
        <TouchableOpacity style={styles.headerBtn} onPress={handleShare} activeOpacity={0.7}>
          <Ionicons name="share-outline" size={22} color="#1A1208" />
        </TouchableOpacity>
      </View>

      {/* Reading progress bar */}
      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: `${progress * 100}%`, backgroundColor: color }]} />
      </View>

      <ScrollView
        style={styles.scroll}
        showsVerticalScrollIndicator={false}
        scrollEventThrottle={16}
        onScroll={(e) => {
          const { contentOffset, contentSize, layoutMeasurement } = e.nativeEvent;
          const maxScroll = contentSize.height - layoutMeasurement.height;
          if (maxScroll > 0) {
            setProgress(Math.min(1, Math.max(0, contentOffset.y / maxScroll)));
          }
        }}>

        {/* Hero image */}
        {image ? (
          <Image source={{ uri: image }} style={styles.image} resizeMode="cover" />
        ) : (
          <View style={[styles.imagePlaceholder, { backgroundColor: color + '22' }]}>
            <Text style={{ fontSize: 72 }}>{emoji}</Text>
          </View>
        )}

        <View style={styles.body}>

          {/* Topic tag + date */}
          <View style={styles.metaRow}>
            <View style={[styles.topicTag, { backgroundColor: color }]}>
              <Text style={styles.topicTagText}>{topic}</Text>
            </View>
            <Text style={styles.metaDate}>{formatDate(date)}</Text>
          </View>

          {/* Title */}
          <Text style={styles.title}>{title}</Text>

          {/* Reading info row */}
          <View style={styles.infoRow}>
            <View style={styles.infoItem}>
              <Ionicons name="time-outline" size={13} color="#C0B8AC" />
              <Text style={styles.infoText}>{readTime}</Text>
            </View>
            {source ? (
              <View style={styles.infoItem}>
                <Ionicons name="newspaper-outline" size={13} color="#C0B8AC" />
                <Text style={styles.infoText} numberOfLines={1}>{source}</Text>
              </View>
            ) : null}
          </View>

          {/* Voice / read aloud button */}
          <TouchableOpacity
            style={[styles.voiceBtn, isSpeaking && styles.voiceBtnActive]}
            onPress={handleSpeak}
            activeOpacity={0.85}>
            <Ionicons
              name={isSpeaking ? 'stop-circle' : 'volume-high'}
              size={26}
              color="white"
              style={{ marginRight: 10 }}
            />
            <View>
              <Text style={styles.voiceBtnLabel}>
                {isSpeaking ? 'Stop Reading' : 'Read Aloud'}
              </Text>
              {!isSpeaking && (
                <Text style={styles.voiceBtnSub}>{readTime} · for kids</Text>
              )}
            </View>
          </TouchableOpacity>

          {/* Summary */}
          <Text style={styles.summary}>{summary}</Text>

          {/* Fun fact */}
          {funFact ? (
            <View style={styles.funFact}>
              <View style={styles.funFactHeader}>
                <Text style={styles.funFactEmoji}>💡</Text>
                <Text style={styles.funFactLabel}>Did you know?</Text>
              </View>
              <Text style={styles.funFactText}>{funFact}</Text>
            </View>
          ) : null}

          {/* Read original button */}
          {url ? (
            <TouchableOpacity
              style={styles.readBtn}
              onPress={() => Linking.openURL(url)}
              activeOpacity={0.85}>
              <Ionicons name="open-outline" size={18} color="white" style={{ marginRight: 8 }} />
              <Text style={styles.readBtnText}>Read Full Article</Text>
            </TouchableOpacity>
          ) : null}

          {/* Share button */}
          <TouchableOpacity style={styles.shareBtn} onPress={handleShare} activeOpacity={0.7}>
            <Ionicons name="share-social-outline" size={18} color="#8A7A65" style={{ marginRight: 8 }} />
            <Text style={styles.shareBtnText}>Share with your child</Text>
          </TouchableOpacity>

          <View style={{ height: 24 + insets.bottom }} />
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF9F0' },

  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: 52,
    paddingHorizontal: 6,
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#EDE5D8',
  },
  headerBtn: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: 13,
    fontWeight: '700',
    color: '#1A1208',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginHorizontal: 4,
  },

  // Progress bar
  progressTrack: { height: 3, backgroundColor: '#EDE5D8' },
  progressFill: { height: 3, borderRadius: 99 },

  scroll: { flex: 1 },

  image: { width: '100%', height: 240 },
  imagePlaceholder: { width: '100%', height: 240, justifyContent: 'center', alignItems: 'center' },

  body: { padding: 20 },

  metaRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  topicTag: { paddingHorizontal: 12, paddingVertical: 4, borderRadius: 99 },
  topicTagText: { color: 'white', fontSize: 12, fontWeight: '700', textTransform: 'uppercase' },
  metaDate: { fontSize: 13, color: '#C0B8AC' },

  title: { fontSize: 24, fontWeight: '800', color: '#1A1208', lineHeight: 32, marginBottom: 12 },

  infoRow: { flexDirection: 'row', gap: 16, marginBottom: 20 },
  infoItem: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  infoText: { fontSize: 12, color: '#C0B8AC', fontWeight: '500' },

  // Voice button
  voiceBtn: {
    backgroundColor: '#1A1208',
    padding: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 24,
    flexDirection: 'row',
    minHeight: 62,
  },
  voiceBtnActive: { backgroundColor: '#FF6B35' },
  voiceBtnLabel: { color: 'white', fontSize: 18, fontWeight: '700' },
  voiceBtnSub: { color: 'rgba(255,255,255,0.5)', fontSize: 12, marginTop: 2 },

  summary: { fontSize: 16, color: '#3D3020', lineHeight: 28, marginBottom: 24 },

  // Fun fact
  funFact: {
    backgroundColor: '#FFFBF0',
    borderWidth: 1.5,
    borderColor: '#FFE66D',
    borderRadius: 14,
    padding: 16,
    marginBottom: 24,
  },
  funFactHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8 },
  funFactEmoji: { fontSize: 20 },
  funFactLabel: { fontSize: 15, fontWeight: '800', color: '#4A3600' },
  funFactText: { fontSize: 14, color: '#7A5C00', lineHeight: 22 },

  // Buttons
  readBtn: {
    backgroundColor: '#FF6B35',
    flexDirection: 'row',
    padding: 17,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12,
    shadowColor: '#FF6B35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 6,
    minHeight: 54,
  },
  readBtnText: { color: 'white', fontSize: 16, fontWeight: '700' },

  shareBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 14,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#EDE5D8',
    backgroundColor: 'white',
    minHeight: 50,
  },
  shareBtnText: { color: '#8A7A65', fontSize: 14, fontWeight: '600' },
});
