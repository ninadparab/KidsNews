import { View, Text, TouchableOpacity, StyleSheet, Linking, ScrollView } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

const FEATURES = [
  {
    icon: '🤖',
    title: 'AI Safety Filtered',
    desc: 'Every story is checked for age-appropriateness before it ever reaches your child.',
  },
  {
    icon: '📅',
    title: 'Updated Every Day',
    desc: 'Fresh stories every morning across 8 topics kids love — science, space, animals, and more.',
  },
  {
    icon: '🔊',
    title: 'Read Aloud Mode',
    desc: 'Kids can listen to any story read aloud at the perfect pace, right in the app.',
  },
  {
    icon: '👧',
    title: 'Ages 6–12',
    desc: 'Stories are rewritten in simple, fun language — no confusing jargon or scary content.',
  },
];

export default function SubscribeScreen() {
  return (
    <ScrollView
      style={styles.container}
      showsVerticalScrollIndicator={false}
      contentContainerStyle={styles.content}>

      {/* Hero card */}
      <View style={styles.hero}>
        <Text style={styles.heroEmoji}>🌟</Text>
        <Text style={styles.heroTitle}>The Daily Whiz</Text>
        <Text style={styles.heroSubtitle}>
          Safe, AI-filtered news for curious kids aged 6–12 — delivered to your inbox every morning.
        </Text>
        <View style={styles.heroBadges}>
          <View style={styles.heroBadge}><Text style={styles.heroBadgeText}>✅ Free forever</Text></View>
          <View style={styles.heroBadge}><Text style={styles.heroBadgeText}>🚫 No ads</Text></View>
          <View style={styles.heroBadge}><Text style={styles.heroBadgeText}>🔒 Kid-safe</Text></View>
        </View>
      </View>

      {/* Feature list */}
      <Text style={styles.sectionLabel}>WHY PARENTS LOVE IT</Text>
      <View style={styles.features}>
        {FEATURES.map((f) => (
          <View key={f.title} style={styles.featureRow}>
            <View style={styles.featureIconWrap}>
              <Text style={styles.featureIconText}>{f.icon}</Text>
            </View>
            <View style={styles.featureBody}>
              <Text style={styles.featureTitle}>{f.title}</Text>
              <Text style={styles.featureDesc}>{f.desc}</Text>
            </View>
          </View>
        ))}
      </View>

      {/* Testimonial */}
      <View style={styles.trustCard}>
        <Text style={styles.trustQuote}>
          "Finally, news my kids can read without me worrying about what they'll see."
        </Text>
        <Text style={styles.trustAttrib}>— Parent of two, ages 8 &amp; 11</Text>
      </View>

      {/* Primary CTA */}
      <TouchableOpacity
        style={styles.primaryBtn}
        activeOpacity={0.85}
        onPress={() => Linking.openURL('https://safekidsnews.com/signup.html')}>
        <Ionicons name="mail" size={20} color="white" style={{ marginRight: 8 }} />
        <Text style={styles.primaryBtnText}>Subscribe Free — No Spam</Text>
      </TouchableOpacity>

      {/* Secondary */}
      <TouchableOpacity
        style={styles.secondaryBtn}
        activeOpacity={0.85}
        onPress={() => Linking.openURL('https://safekidsnews.com')}>
        <Ionicons name="globe-outline" size={18} color="#1A1208" style={{ marginRight: 8 }} />
        <Text style={styles.secondaryBtnText}>Browse on Web</Text>
      </TouchableOpacity>

      <Text style={styles.footerNote}>Unsubscribe any time · We never share your email</Text>

      {/* Privacy and Links */}
      <View style={styles.footerLinks}>
        <TouchableOpacity onPress={() => Linking.openURL('https://safekidsnews.com/privacy.html')}>
          <Text style={styles.footerLink}>Privacy Policy</Text>
        </TouchableOpacity>
        <Text style={styles.footerDivider}>·</Text>
        <TouchableOpacity onPress={() => Linking.openURL('https://safekidsnews.com')}>
          <Text style={styles.footerLink}>How It Works</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FFF9F0' },
  content: { padding: 20, paddingBottom: 48 },

  hero: {
    alignItems: 'center',
    backgroundColor: '#1A1208',
    borderRadius: 20,
    padding: 28,
    marginBottom: 28,
  },
  heroEmoji: { fontSize: 56, marginBottom: 12 },
  heroTitle: { fontSize: 28, fontWeight: '800', color: '#FFE66D', marginBottom: 10, letterSpacing: -0.5 },
  heroSubtitle: {
    fontSize: 15,
    color: 'rgba(255,255,255,0.65)',
    textAlign: 'center',
    lineHeight: 23,
    marginBottom: 18,
  },
  heroBadges: { flexDirection: 'row', gap: 8, flexWrap: 'wrap', justifyContent: 'center' },
  heroBadge: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.15)',
    paddingHorizontal: 12,
    paddingVertical: 5,
    borderRadius: 99,
  },
  heroBadgeText: { color: 'rgba(255,255,255,0.85)', fontSize: 12, fontWeight: '600' },

  sectionLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#C0B8AC',
    letterSpacing: 0.8,
    marginBottom: 12,
  },
  features: { gap: 12, marginBottom: 24 },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: 'white',
    borderRadius: 14,
    padding: 16,
    borderWidth: 1,
    borderColor: '#EDE5D8',
    gap: 14,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 4,
    elevation: 2,
  },
  featureIconWrap: {
    width: 46,
    height: 46,
    borderRadius: 13,
    backgroundColor: '#FFF9F0',
    justifyContent: 'center',
    alignItems: 'center',
    flexShrink: 0,
    borderWidth: 1,
    borderColor: '#EDE5D8',
  },
  featureIconText: { fontSize: 22 },
  featureBody: { flex: 1 },
  featureTitle: { fontSize: 15, fontWeight: '700', color: '#1A1208', marginBottom: 3 },
  featureDesc: { fontSize: 13, color: '#8A7A65', lineHeight: 19 },

  trustCard: {
    backgroundColor: '#FFF3EC',
    borderLeftWidth: 3,
    borderLeftColor: '#FF6B35',
    borderRadius: 12,
    padding: 16,
    marginBottom: 28,
  },
  trustQuote: { fontSize: 15, color: '#3D2010', fontStyle: 'italic', lineHeight: 23, marginBottom: 8 },
  trustAttrib: { fontSize: 12, color: '#FF6B35', fontWeight: '700' },

  primaryBtn: {
    backgroundColor: '#FF6B35',
    padding: 17,
    borderRadius: 14,
    alignItems: 'center',
    marginBottom: 12,
    flexDirection: 'row',
    justifyContent: 'center',
    shadowColor: '#FF6B35',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 6,
  },
  primaryBtnText: { color: 'white', fontSize: 16, fontWeight: '700' },

  secondaryBtn: {
    backgroundColor: 'white',
    padding: 16,
    borderRadius: 14,
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#EDE5D8',
    marginBottom: 20,
    flexDirection: 'row',
    justifyContent: 'center',
  },
  secondaryBtnText: { color: '#1A1208', fontSize: 15, fontWeight: '600' },

  footerNote: { textAlign: 'center', fontSize: 12, color: '#C0B8AC', fontWeight: '500' },

  footerLinks: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 14,
    gap: 8,
  },
  footerLink: { fontSize: 12, color: '#FF6B35', fontWeight: '600', textDecorationLine: 'underline' },
  footerDivider: { color: '#C0B8AC' },
});
