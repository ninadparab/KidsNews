import { useState, useEffect, useRef } from 'react';
import {
  StyleSheet, FlatList, View, Text, TouchableOpacity,
  Image, ActivityIndicator, RefreshControl, ScrollView, Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import Animated, {
  useSharedValue, useAnimatedStyle, interpolate,
  Extrapolate,
} from 'react-native-reanimated';

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
const HERO_HEIGHT = 240;

interface Article {
  id: string;
  kid_title: string;
  kid_summary: string;
  did_you_know: string;
  topics: string[];
  url: string;
  url_to_image: string;
  date: string;
  source?: string;
  age_group?: string;
}

function getReadTime(text: string): string {
  if (!text) return '1 min read';
  const words = text.trim().split(/\s+/).length;
  return `${Math.max(1, Math.ceil(words / 150))} min read`;
}

function getSourceName(article: Article): string {
  if (article.source) return article.source;
  if (!article.url) return '';
  try {
    return new URL(article.url).hostname.replace(/^www\./, '').split('.')[0];
  } catch { return ''; }
}

function formatDate(dateStr: string): string {
  try {
    return new Date(dateStr + 'T12:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  } catch { return dateStr; }
}

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning!';
  if (h < 17) return 'Good afternoon!';
  return 'Good evening!';
}

function getLastUpdatedText(date: Date | null): string {
  if (!date) return '';
  const mins = Math.floor((Date.now() - date.getTime()) / 60000);
  if (mins < 1) return 'Just updated';
  if (mins === 1) return 'Updated 1 min ago';
  return `Updated ${mins} min ago`;
}

export default function HomeScreen() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [filtered, setFiltered] = useState<Article[]>([]);
  const [activeTopic, setActiveTopic] = useState('All');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const activeTopicRef = useRef(activeTopic);
  activeTopicRef.current = activeTopic;
  const scrollY = useSharedValue(0);
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
                value: { stringValue: cutoff },
              },
            },
            orderBy: [{ field: { fieldPath: 'date' }, direction: 'DESCENDING' }],
            limit: 50,
          },
        }),
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
            source: f.source?.stringValue || '',
            age_group: f.age_group?.stringValue || '',
          };
        });

      setArticles(docs);
      const topic = activeTopicRef.current;
      setFiltered(topic === 'All' ? docs : docs.filter(a => a.topics?.includes(topic)));
      setLastUpdated(new Date());
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
    setFiltered(topic === 'All' ? articles : articles.filter(a => a.topics?.includes(topic)));
  }

  function getTopicCount(topic: string): number {
    return topic === 'All' ? articles.length : articles.filter(a => a.topics?.includes(topic)).length;
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
        source: getSourceName(article),
      },
    });
  }

  // Animated style for sticky filters
  const filterAnimStyle = useAnimatedStyle(() => {
    const translateY = interpolate(scrollY.value, [0, HERO_HEIGHT], [0, HERO_HEIGHT], Extrapolate.CLAMP);
    return { transform: [{ translateY }] };
  });

  const HeroSection = () => {
    const today = new Date().toLocaleDateString('en-US', {
      weekday: 'long', month: 'long', day: 'numeric',
    });

    return (
      <View style={styles.hero}>
        <View style={styles.heroTop}>
          <View style={{ flex: 1 }}>
            <Text style={styles.heroGreeting}>{getGreeting()}</Text>
            <Text style={styles.heroDate}>{today}</Text>
          </View>
          <TouchableOpacity style={styles.searchBtn} activeOpacity={0.7}>
            <Ionicons name="search-outline" size={20} color="#FFE66D" />
          </TouchableOpacity>
        </View>

        <Text style={styles.heroTagline}>Here's today's kid-safe news ✨</Text>

        {/* Trust signals */}
        <View style={styles.trustSignals}>
          <View style={styles.trustSignal}>
            <Text style={styles.trustIcon}>🤖</Text>
            <Text style={styles.trustLabel}>AI Safety</Text>
            <Text style={styles.trustSubLabel}>Filtered</Text>
          </View>
          <View style={styles.trustDivider} />
          <View style={styles.trustSignal}>
            <Text style={styles.trustIcon}>📅</Text>
            <Text style={styles.trustLabel}>Updated</Text>
            <Text style={styles.trustSubLabel}>Daily</Text>
          </View>
          <View style={styles.trustDivider} />
          <View style={styles.trustSignal}>
            <Text style={styles.trustIcon}>👧</Text>
            <Text style={styles.trustLabel}>Ages</Text>
            <Text style={styles.trustSubLabel}>6–12</Text>
          </View>
        </View>

        <View style={styles.heroStats}>
          <View style={styles.heroStat}>
            <Text style={styles.heroStatNum}>{articles.length}</Text>
            <Text style={styles.heroStatLabel}>Stories</Text>
          </View>
          <View style={styles.heroStatDivider} />
          <View style={styles.heroStat}>
            <Text style={styles.heroStatNum}>8</Text>
            <Text style={styles.heroStatLabel}>Topics</Text>
          </View>
          <View style={styles.heroStatDivider} />
          <View style={styles.heroStat}>
            <Text style={styles.heroStatNum}>100%</Text>
            <Text style={styles.heroStatLabel}>Kid Safe</Text>
          </View>
        </View>
      </View>
    );
  };

  const FilterSection = () => (
    <View style={styles.filterWrap}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        contentContainerStyle={styles.filterList}>
        {TOPICS.map(topic => {
          const active = activeTopic === topic;
          const count = getTopicCount(topic);
          return (
            <TouchableOpacity
              key={topic}
              style={[styles.filterChip, active && styles.filterChipActive]}
              onPress={() => filterByTopic(topic)}
              activeOpacity={0.75}>
              <Text style={[styles.filterChipText, active && styles.filterChipTextActive]}>
                {topic === 'All' ? '✨ All' : `${TOPIC_EMOJIS[topic]} ${topic}`}
              </Text>
              <View style={[styles.countBadge, active && styles.countBadgeActive]}>
                <Text style={[styles.countText, active && styles.countTextActive]}>{count}</Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </ScrollView>
    </View>
  );

  const renderCard = ({ item }: { item: Article }) => {
    const topic = item.topics?.[0] || 'Science';
    const color = TOPIC_COLORS[topic] || '#888';
    const emoji = TOPIC_EMOJIS[topic] || '📰';
    const readTime = getReadTime(item.kid_summary);
    const source = getSourceName(item);

    return (
      <TouchableOpacity style={styles.card} onPress={() => openArticle(item)} activeOpacity={0.85}>
        {item.url_to_image ? (
          <Image
            source={{ uri: item.url_to_image }}
            style={styles.cardImage}
            resizeMode="cover"
          />
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
            <View style={styles.cardMetaRight}>
              <Text style={styles.cardDate}>{formatDate(item.date)}</Text>
              <Text style={styles.readTime}> · {readTime}</Text>
            </View>
          </View>

          <Text style={styles.cardTitle} numberOfLines={2}>{item.kid_title}</Text>
          <Text style={styles.cardSummary} numberOfLines={3}>{item.kid_summary}</Text>

          {item.did_you_know ? (
            <View style={styles.funFact}>
              <Text style={styles.funFactText}>
                💡 <Text style={styles.funFactBold}>Did you know?</Text> {item.did_you_know}
              </Text>
            </View>
          ) : null}

          <View style={styles.cardFooter}>
            <Text style={styles.cardSource} numberOfLines={1}>
              {source ? `📰 ${source}` : ''}
            </Text>
            <View style={styles.cardFooterRight}>
              {item.age_group ? (
                <View style={styles.ageBadge}>
                  <Text style={styles.ageBadgeText}>Ages {item.age_group}</Text>
                </View>
              ) : null}
              <Ionicons name="bookmark-outline" size={18} color="#C8BFB5" style={{ marginLeft: 8 }} />
            </View>
          </View>
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
      <HeroSection />

      <Animated.View style={[styles.stickyFilterContainer, filterAnimStyle]}>
        <FilterSection />
        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>
            {activeTopic === 'All' ? 'Latest Stories' : `${TOPIC_EMOJIS[activeTopic]} ${activeTopic}`}
          </Text>
          <Text style={styles.lastUpdated}>{getLastUpdatedText(lastUpdated)}</Text>
        </View>
      </Animated.View>

      <FlatList
        style={styles.list}
        data={filtered}
        keyExtractor={item => item.id}
        renderItem={renderCard}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        scrollEventThrottle={16}
        onScroll={(e) => {
          scrollY.value = e.nativeEvent.contentOffset.y;
        }}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => { setRefreshing(true); fetchArticles(); }}
            tintColor="#FF6B35"
            colors={['#FF6B35']}
          />
        }
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={{ fontSize: 48 }}>🔍</Text>
            <Text style={styles.emptyText}>No stories found</Text>
            <Text style={styles.emptySubtext}>Try a different topic filter</Text>
          </View>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF9F0' },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 32, backgroundColor: '#FFF9F0' },
  loadingText: { marginTop: 12, color: '#8A7A65', fontSize: 14 },

  // Hero
  hero: {
    backgroundColor: '#1A1208',
    padding: 20,
    paddingBottom: 22,
    paddingTop: Platform.OS === 'ios' ? 8 : 12,
  },
  heroTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  heroGreeting: {
    color: '#FFE66D',
    fontSize: 12,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    marginBottom: 3,
  },
  heroDate: { color: 'white', fontSize: 16, fontWeight: '700' },
  heroTagline: { color: 'rgba(255,255,255,0.55)', fontSize: 13, marginBottom: 16 },
  searchBtn: {
    width: 44,
    height: 44,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 12,
    marginLeft: 12,
  },

  // Trust signals
  trustSignals: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    backgroundColor: 'rgba(255,255,255,0.06)',
    borderRadius: 12,
    paddingVertical: 14,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  trustSignal: { alignItems: 'center', flex: 1 },
  trustIcon: { fontSize: 20, marginBottom: 5 },
  trustLabel: { color: 'white', fontSize: 12, fontWeight: '700', letterSpacing: 0.3 },
  trustSubLabel: { color: 'rgba(255,255,255,0.5)', fontSize: 10, marginTop: 2 },
  trustDivider: { width: 1, height: 24, backgroundColor: 'rgba(255,255,255,0.15)' },

  // Stats
  heroStats: { flexDirection: 'row', alignItems: 'center' },
  heroStat: { flex: 1, alignItems: 'center' },
  heroStatNum: { color: '#FFE66D', fontSize: 22, fontWeight: '800' },
  heroStatLabel: {
    color: 'rgba(255,255,255,0.45)',
    fontSize: 10,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginTop: 2,
  },
  heroStatDivider: { width: 1, height: 32, backgroundColor: 'rgba(255,255,255,0.1)' },

  // Sticky filter container
  stickyFilterContainer: {
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#EDE5D8',
  },

  // Filters
  filterWrap: {
    backgroundColor: 'white',
    borderBottomWidth: 1,
    borderBottomColor: '#EDE5D8',
  },
  filterList: { paddingHorizontal: 12, paddingVertical: 10, gap: 8 },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 13,
    paddingVertical: 8,
    borderRadius: 99,
    borderWidth: 1.5,
    borderColor: '#EDE5D8',
    backgroundColor: 'white',
    gap: 6,
    minHeight: 36,
  },
  filterChipActive: {
    backgroundColor: '#1A1208',
    borderColor: '#1A1208',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.18,
    shadowRadius: 6,
    elevation: 4,
  },
  filterChipText: { fontSize: 13, fontWeight: '600', color: '#8A7A65' },
  filterChipTextActive: { color: 'white' },
  countBadge: {
    backgroundColor: 'rgba(0,0,0,0.08)',
    borderRadius: 99,
    paddingHorizontal: 6,
    paddingVertical: 1,
    minWidth: 20,
    alignItems: 'center',
  },
  countBadgeActive: { backgroundColor: 'rgba(255,255,255,0.2)' },
  countText: { fontSize: 10, fontWeight: '700', color: '#8A7A65' },
  countTextActive: { color: 'white' },

  // Section header
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 12,
  },
  sectionTitle: { fontSize: 16, fontWeight: '700', color: '#1A1208' },
  lastUpdated: { fontSize: 11, color: '#C0B8AC' },

  // List
  list: { flex: 1, backgroundColor: '#FFF9F0' },
  listContent: { paddingHorizontal: 16, paddingTop: 12, paddingBottom: 32, gap: 16 },

  // Card
  card: {
    backgroundColor: 'white',
    borderRadius: 18,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: '#EDE5D8',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 4,
  },
  cardImage: { width: '100%', height: 185 },
  cardImagePlaceholder: { width: '100%', height: 185, justifyContent: 'center', alignItems: 'center' },
  cardImageEmoji: { fontSize: 56 },
  cardBody: { padding: 16 },
  cardMeta: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  cardMetaRight: { flexDirection: 'row', alignItems: 'center' },
  topicTag: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 99 },
  topicTagText: {
    color: 'white',
    fontSize: 11,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  cardDate: { fontSize: 11, color: '#C0B8AC', fontWeight: '500' },
  readTime: { fontSize: 11, color: '#C0B8AC', fontWeight: '500' },
  cardTitle: { fontSize: 17, fontWeight: '700', color: '#1A1208', marginBottom: 8, lineHeight: 24 },
  cardSummary: { fontSize: 14, color: '#5a5040', lineHeight: 21, marginBottom: 12 },
  funFact: {
    backgroundColor: '#FFFBF0',
    borderLeftWidth: 3,
    borderLeftColor: '#FFE66D',
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 12,
  },
  funFactText: { fontSize: 13, color: '#6B4F00', lineHeight: 19 },
  funFactBold: { fontWeight: '700', color: '#4A3600' },
  cardFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 10,
    borderTopWidth: 1,
    borderTopColor: '#EDE5D8',
  },
  cardSource: { fontSize: 11, color: '#C0B8AC', fontWeight: '600', textTransform: 'capitalize', flex: 1 },
  cardFooterRight: { flexDirection: 'row', alignItems: 'center' },
  ageBadge: {
    backgroundColor: '#F5F0E8',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 99,
  },
  ageBadgeText: { fontSize: 11, color: '#8A7A65' },

  // Empty
  empty: { alignItems: 'center', padding: 48 },
  emptyText: { fontSize: 18, fontWeight: '700', color: '#1A1208', marginTop: 12 },
  emptySubtext: { fontSize: 14, color: '#8A7A65', marginTop: 4 },
});
