import { useState, useEffect } from 'react';
import {
  StyleSheet, FlatList, View, Text, TouchableOpacity,
  Image, ScrollView, ActivityIndicator, RefreshControl
} from 'react-native';
import { useRouter } from 'expo-router';

const FIREBASE_PROJECT_ID = 'kidsnews-f9c81';

const TOPIC_EMOJIS: Record<string, string> = {
  Science: '🔬', Space: '🚀', Animals: '🦁', Sports: '⚽',
  Technology: '💻', Weather: '🌤️', Arts: '🎨', Environment: '🌿',
};

const TOPIC_COLORS: Record<string, string> = {
  Science: '#4ECDC4', Space: '#9B5DE5', Animals: '#00B4D8',
  Sports: '#FF6B35', Technology: '#06D6A0', Weather: '#118AB2',
  Arts: '#EF476F', Environment: '#57CC99',
};

const TOPICS = ['All', 'Science', 'Space', 'Animals', 'Sports', 'Technology', 'Weather', 'Arts', 'Environment'];

interface Article {
  id: string;
  kid_title: string;
  kid_summary: string;
  did_you_know: string;
  topics: string[];
  url: string;
  url_to_image: string;
  date: string;
}

export default function HomeScreen() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [filtered, setFiltered] = useState<Article[]>([]);
  const [activeTopic, setActiveTopic] = useState('All');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const router = useRouter();

  async function fetchArticles() {
    try {
      const sevenDaysAgo = new Date();
      sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
      const cutoff = sevenDaysAgo.toISOString().split('T')[0];

      const url = `https://firestore.googleapis.com/v1/projects/${FIREBASE_PROJECT_ID}/databases/(default)/documents:runQuery`;
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          structuredQuery: {
            from: [{ collectionId: 'articles' }],
            where: {
              fieldFilter: {
                field: { fieldPath: 'date' },
                op: 'GREATER_THAN_OR_EQUAL',
                value: { stringValue: cutoff }
              }
            },
            orderBy: [{ field: { fieldPath: 'date' }, direction: 'DESCENDING' }],
            limit: 50
          }
        })
      });

      const data = await response.json();
      const docs: Article[] = data
        .filter((item: any) => item.document)
        .map((item: any) => {
          const f = item.document.fields;
          return {
            id: item.document.name.split('/').pop(),
            kid_title: f.kid_title?.stringValue || '',
            kid_summary: f.kid_summary?.stringValue || '',
            did_you_know: f.did_you_know?.stringValue || '',
            topics: f.topics?.arrayValue?.values?.map((v: any) => v.stringValue) || ['Science'],
            url: f.url?.stringValue || '',
            url_to_image: f.url_to_image?.stringValue || '',
            date: f.date?.stringValue || '',
          };
        });

      setArticles(docs);
      setFiltered(docs);
    } catch (err) {
      console.error('Failed to fetch articles:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => { fetchArticles(); }, []);

  function filterByTopic(topic: string) {
    setActiveTopic(topic);
    if (topic === 'All') {
      setFiltered(articles);
    } else {
      setFiltered(articles.filter(a => a.topics?.includes(topic)));
    }
  }

  function openArticle(article: Article) {
    router.push({
      pathname: '/article',
      params: {
        title: article.kid_title,
        summary: article.kid_summary,
        funFact: article.did_you_know,
        url: article.url,
        image: article.url_to_image,
        topic: article.topics?.[0] || 'Science',
        date: article.date,
      }
    });
  }

  const renderCard = ({ item }: { item: Article }) => {
    const topic = item.topics?.[0] || 'Science';
    const color = TOPIC_COLORS[topic] || '#888';
    const emoji = TOPIC_EMOJIS[topic] || '📰';

    return (
      <TouchableOpacity style={styles.card} onPress={() => openArticle(item)} activeOpacity={0.85}>
        {item.url_to_image ? (
          <Image source={{ uri: item.url_to_image }} style={styles.cardImage} />
        ) : (
          <View style={[styles.cardImagePlaceholder, { backgroundColor: color + '22' }]}>
            <Text style={styles.cardImageEmoji}>{emoji}</Text>
          </View>
        )}
        <View style={styles.cardBody}>
          <View style={styles.cardMeta}>
            <View style={[styles.topicTag, { backgroundColor: color }]}>
              <Text style={styles.topicTagText}>{topic}</Text>
            </View>
            <Text style={styles.cardDate}>{item.date}</Text>
          </View>
          <Text style={styles.cardTitle} numberOfLines={2}>{item.kid_title}</Text>
          <Text style={styles.cardSummary} numberOfLines={3}>{item.kid_summary}</Text>
          {item.did_you_know ? (
            <View style={styles.funFact}>
              <Text style={styles.funFactText}>💡 {item.did_you_know}</Text>
            </View>
          ) : null}
        </View>
      </TouchableOpacity>
    );
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#FF6B35" />
        <Text style={styles.loadingText}>Loading stories...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterBar}>
        {TOPICS.map(topic => (
          <TouchableOpacity
            key={topic}
            style={[styles.filterChip, activeTopic === topic && styles.filterChipActive]}
            onPress={() => filterByTopic(topic)}>
            <Text style={[styles.filterChipText, activeTopic === topic && styles.filterChipTextActive]}>
              {topic === 'All' ? '✨ All' : `${TOPIC_EMOJIS[topic]} ${topic}`}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <Text style={styles.articleCount}>{filtered.length} stories</Text>

      <FlatList
        data={filtered}
        keyExtractor={item => item.id}
        renderItem={renderCard}
        contentContainerStyle={styles.list}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); fetchArticles(); }}
            tintColor="#FF6B35"
          />
        }
        ListEmptyComponent={
          <View style={styles.centered}>
            <Text style={{ fontSize: 48 }}>🔍</Text>
            <Text style={styles.emptyText}>No stories found</Text>
            <Text style={styles.emptySubtext}>Try a different topic</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF9F0' },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32 },
  loadingText: { marginTop: 12, color: '#888', fontSize: 14 },
  filterBar: { backgroundColor: 'white', paddingVertical: 10, paddingHorizontal: 12, borderBottomWidth: 1, borderBottomColor: '#EDE5D8', flexGrow: 0 },
  filterChip: { paddingHorizontal: 16, paddingVertical: 6, borderRadius: 99, borderWidth: 1.5, borderColor: '#EDE5D8', marginRight: 8, backgroundColor: 'white' },
  filterChipActive: { backgroundColor: '#1A1208', borderColor: '#1A1208' },
  filterChipText: { fontSize: 13, fontWeight: '500', color: '#888' },
  filterChipTextActive: { color: 'white' },
  articleCount: { fontSize: 12, color: '#888', paddingHorizontal: 16, paddingVertical: 8 },
  list: { padding: 16, gap: 16 },
  card: { backgroundColor: 'white', borderRadius: 16, overflow: 'hidden', borderWidth: 1, borderColor: '#EDE5D8', shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.06, shadowRadius: 8, elevation: 3 },
  cardImage: { width: '100%', height: 180 },
  cardImagePlaceholder: { width: '100%', height: 180, justifyContent: 'center', alignItems: 'center' },
  cardImageEmoji: { fontSize: 56 },
  cardBody: { padding: 16 },
  cardMeta: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  topicTag: { paddingHorizontal: 10, paddingVertical: 3, borderRadius: 99 },
  topicTagText: { color: 'white', fontSize: 11, fontWeight: '700', textTransform: 'uppercase', letterSpacing: 0.5 },
  cardDate: { fontSize: 12, color: '#888' },
  cardTitle: { fontSize: 17, fontWeight: '700', color: '#1A1208', marginBottom: 8, lineHeight: 24 },
  cardSummary: { fontSize: 14, color: '#555', lineHeight: 20, marginBottom: 10 },
  funFact: { backgroundColor: '#FFFBF0', borderWidth: 1, borderColor: '#FFE66D', borderRadius: 8, padding: 10 },
  funFactText: { fontSize: 13, color: '#7A5C00', lineHeight: 18 },
  emptyText: { fontSize: 18, fontWeight: '700', color: '#1A1208', marginTop: 12 },
  emptySubtext: { fontSize: 14, color: '#888', marginTop: 4 },
});
