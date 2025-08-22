import { setUserProvider } from "@/lib/api";
import { setV2UserProvider } from "@/lib/researchApi";
import { useEffect } from "react";
import { useAuth } from "react-oidc-context";

export const UserSet = () => {
  const auth = useAuth();

  console.log('🚀 UserSet component rendered');

  useEffect(() => {
    const timestamp = new Date().toISOString();
    console.group(`🔍 [${timestamp}] UserSet - OIDC Authentication State Check`);
    
    console.log('🔐 Auth object:', {
      isAuthenticated: auth.isAuthenticated,
      isLoading: auth.isLoading,
      hasUser: !!auth.user,
      error: auth.error
    });
    
    if (auth.user) {
      console.log('👤 User profile:', {
        email: auth.user.profile?.email,
        sub: auth.user.profile?.sub,
        preferred_username: auth.user.profile?.preferred_username,
        roles: auth.user.profile?.roles
      });
      
      console.log('🎫 Token info:', {
        hasAccessToken: !!auth.user.access_token,
        tokenLength: auth.user.access_token?.length || 0,
        tokenPreview: auth.user.access_token?.substring(0, 20) + '...',
        expiresAt: auth.user.expires_at ? new Date(auth.user.expires_at * 1000).toISOString() : 'N/A',
        isExpired: auth.user.expires_at ? auth.user.expires_at < Date.now() / 1000 : 'Unknown'
      });
      
      // Check localStorage storage
      const expectedKey = `oidc.user:${window.location.origin}/oauth_callback`;
      const storedValue = localStorage.getItem(expectedKey);
      console.log('💾 localStorage check:', {
        expectedKey,
        hasStoredValue: !!storedValue,
        storedValueLength: storedValue?.length || 0
      });
    } else {
      console.log('❌ No user object available');
      
      // Debug localStorage for any OIDC keys
      console.log('🗄️ Checking ALL localStorage for OIDC keys:');
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key?.includes('oidc')) {
          console.log(`   Found OIDC key: ${key}`);
        }
      }
    }
    
    if (auth.error) {
      console.error('🚨 OIDC Error:', auth.error);
    }
    
    if (auth.isAuthenticated) {
      console.log('✅ User is authenticated - setting user providers');
      // Set the user provider for v1 API
      setUserProvider(() => Promise.resolve(auth.user ?? null));
      
      // Set the user provider for v2 API
      setV2UserProvider(() => Promise.resolve(auth.user ?? null));
    } else {
      console.log('❌ User is NOT authenticated');
    }
    
    console.groupEnd();
  }, [auth.isAuthenticated, auth.user, auth.isLoading, auth.error]);

  return null;
};
