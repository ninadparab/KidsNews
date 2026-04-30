import { Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { View, Text, Platform, StyleSheet } from 'react-native';

function TabIcon({ name, color, focused }: { name: any; color: string; focused: boolean }) {
  return (
    <View style={[styles.iconWrap, focused && styles.iconWrapActive]}>
      <Ionicons name={name} size={22} color={color} />
    </View>
  );
}

function HeaderLogo() {
  return (
    <View style={styles.headerLogo}>
      <Text style={styles.headerLogoText}>🌟 The Daily Whiz</Text>
      <Text style={styles.headerTagline}>Safe, AI-filtered news for curious kids</Text>
    </View>
  );
}

function HeaderRight() {
  return (
    <View style={styles.headerRight}>
      <View style={styles.trustBadge}>
        <Text style={styles.trustBadgeText}>✅ 100% Kid Safe</Text>
      </View>
    </View>
  );
}

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#FF6B35',
        tabBarInactiveTintColor: '#8A7A65',
        tabBarStyle: styles.tabBar,
        tabBarLabelStyle: styles.tabLabel,
        headerStyle: styles.header,
        headerTintColor: '#FFE66D',
        headerTitleStyle: styles.headerTitle,
        headerShadowVisible: false,
      }}>
      <Tabs.Screen
        name="index"
        options={{
          headerTitle: () => <HeaderLogo />,
          headerRight: () => <HeaderRight />,
          headerRightContainerStyle: { paddingRight: 12 },
          headerLeftContainerStyle: { paddingLeft: 0 },
          tabBarLabel: 'News',
          tabBarIcon: ({ color, focused }) => (
            <TabIcon name={focused ? 'newspaper' : 'newspaper-outline'} color={color} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="explore"
        options={{
          title: '🌟 The Daily Whiz',
          tabBarLabel: 'Subscribe',
          tabBarIcon: ({ color, focused }) => (
            <TabIcon name={focused ? 'mail' : 'mail-outline'} color={color} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="article"
        options={{
          href: null,
          headerShown: false,
        }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  header: {
    backgroundColor: '#1A1208',
    height: Platform.OS === 'ios' ? 100 : 90,
  },
  headerTitle: {
    fontWeight: '800',
    fontSize: 18,
    color: '#FFE66D',
    letterSpacing: -0.3,
  },
  headerLogo: {
    flex: 1,
    justifyContent: 'center',
  },
  headerLogoText: {
    fontWeight: '800',
    fontSize: 16,
    color: '#FFE66D',
    letterSpacing: -0.3,
  },
  headerTagline: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.55)',
    fontWeight: '500',
    marginTop: 2,
    letterSpacing: 0.3,
  },
  headerRight: {
    alignItems: 'flex-end',
  },
  trustBadge: {
    backgroundColor: 'rgba(255,230,109,0.15)',
    borderWidth: 1,
    borderColor: 'rgba(255,230,109,0.35)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 99,
  },
  trustBadgeText: {
    color: '#FFE66D',
    fontSize: 11,
    fontWeight: '700',
  },
  tabBar: {
    backgroundColor: '#1A1208',
    borderTopColor: 'rgba(255,255,255,0.08)',
    borderTopWidth: 1,
    height: Platform.OS === 'ios' ? 84 : 64,
    paddingBottom: Platform.OS === 'ios' ? 26 : 8,
    paddingTop: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.25,
    shadowRadius: 12,
    elevation: 20,
  },
  tabLabel: {
    fontSize: 11,
    fontWeight: '600',
    marginTop: 1,
  },
  iconWrap: {
    width: 44,
    height: 32,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 99,
  },
  iconWrapActive: {
    backgroundColor: 'rgba(255,107,53,0.18)',
  },
});
