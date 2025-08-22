/*
 * Licensed to the Apache Software Foundation (ASF) under one
 * or more contributor license agreements. See the NOTICE file
 * distributed with this work for additional information
 * regarding copyright ownership. The ASF licenses this file
 * to you under the Apache License, Version 2.0 (the
 * "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 *
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing,
 *  software distributed under the License is distributed on an
 *  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
 *  KIND, either express or implied. See the License for the
 *  specific language governing permissions and limitations
 *  under the License.
 */

import {useColorMode} from "./components/ui/color-mode";
import {Route, Routes, useLocation, useNavigate} from "react-router-dom";
import Home from "./components/home";
import {Models} from "./components/models";
import {Datasets} from "./components/datasets";
import ResourceDetails from "./components/resources/ResourceDetails";
import Notebooks from "./components/notebooks";
import Repositories from "./components/repositories";
import {Login} from "./components/auth/UserLoginPage";
import {Signup} from "./components/auth/SignupPage";
import {OAuthCallback} from "./components/auth/OAuthCallback";
import ProtectedComponent from "./components/auth/ProtectedComponent";
import {AuthProvider, AuthProviderProps} from "react-oidc-context";
import {useEffect, useState} from "react";
import NavBarFooterLayout from "./layouts/NavBarFooterLayout";
import {NewLandingPage} from "./components/home/NewLandingPage";
import {APP_REDIRECT_URI, CLIENT_ID, OPENID_CONFIG_URL,} from "./lib/constants";
import {WebStorageStateStore} from "oidc-client-ts";
import {Resources} from "./components/resources";
import {UserSet} from "./components/auth/UserSet";
import {Toaster} from "./components/ui/toaster";
import {Events} from "./components/events";
import {AddRepoMaster} from "./components/add/AddRepoMaster";
import {Add} from "./components/add";
import {AddProjectMaster} from "./components/add/AddProjectMaster";
import {StarredResourcesPage} from "@/components/resources/StarredResourcesPage.tsx";
import {Catalog} from "./components/catalog";
import {SidebarLayout} from "./layouts/SidebarLayout";
import {ResourceDetail} from "./components/resources/ResourceDetail";
import SearchResults from "./components/search/SearchResults";
import {AddModelForm} from "./components/models/AddModelForm";
import {AddDatasetForm} from "./components/datasets/AddDatasetForm";
import {DatasetDetail} from "./components/datasets/DatasetDetail";
import {ModelDetail} from "./components/models/ModelDetail";
import {NotebookDetail} from "./components/notebooks/NotebookDetail";
import {RepositoryDetail} from "./components/repositories/RepositoryDetail";
import {AddComputeResourceForm} from "./components/resources/AddComputeResourceForm";
import {AddStorageResourceForm} from "./components/resources/AddStorageResourceForm";
import {AddNotebookForm} from "./components/notebooks/AddNotebookForm";
import {AddRepositoryForm} from "./components/repositories/AddRepositoryForm";

function App() {
  console.log('🚨 App.tsx function is executing');
  
  const colorMode = useColorMode();
  const navigate = useNavigate();
  const location = useLocation();
  const [oidcConfig, setOidcConfig] = useState<AuthProviderProps | null>(null);

  if (colorMode.colorMode === "dark") {
    colorMode.toggleColorMode();
  }

  useEffect(() => {
    const fetchOidcConfig = async () => {
      const timestamp = new Date().toISOString();
      console.group(`🔧 [${timestamp}] OIDC Configuration Setup`);
      
      try {
        console.log('🌐 OIDC Config URL:', OPENID_CONFIG_URL);
        console.log('🆔 Client ID:', CLIENT_ID);
        console.log('↩️ Redirect URI:', APP_REDIRECT_URI);
        console.log('🏠 Current Origin:', window.location.origin);
        
        console.log('📡 Fetching OIDC configuration...');
        const response = await fetch(OPENID_CONFIG_URL);
        
        if (!response.ok) {
          throw new Error(`OIDC config fetch failed: ${response.status} ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('✅ OIDC config fetched successfully');
        console.log('🔗 Authorization endpoint:', data.authorization_endpoint);
        console.log('🎫 Token endpoint:', data.token_endpoint);
        console.log('🔐 JWKS URI:', data.jwks_uri);
        console.log('👤 UserInfo endpoint:', data.userinfo_endpoint);

        const redirectUri = APP_REDIRECT_URI;

        const theConfig: AuthProviderProps = {
          authority: `https://auth.dev.cybershuttle.org/realms/default`,
          client_id: CLIENT_ID,
          redirect_uri: redirectUri,
          response_type: "code",
          scope: "openid email",
          metadata: {
            authorization_endpoint: data.authorization_endpoint,
            token_endpoint: data.token_endpoint,
            revocation_endpoint: data.revocation_endpoint,
            introspection_endpoint: data.introspection_endpoint,
            userinfo_endpoint: data.userinfo_endpoint,
            jwks_uri: data.jwks_uri,
          },
          userStore: new WebStorageStateStore({store: window.localStorage}),
          automaticSilentRenew: true,
          onSigninCallback: (user) => {
            console.group(`🎉 [${new Date().toISOString()}] OIDC Signin Callback`);
            console.log('👤 User authenticated:', user?.profile?.email || user?.profile?.sub);
            console.log('🎫 Access token received:', user?.access_token ? 'YES' : 'NO');
            console.log('🕐 Token expires at:', user?.expires_at ? new Date(user.expires_at * 1000).toISOString() : 'N/A');
            console.log('🔄 Refresh token available:', user?.refresh_token ? 'YES' : 'NO');
            console.groupEnd();
          },
          onUserLoaded: (user) => {
            console.group(`👤 [${new Date().toISOString()}] OIDC User Loaded`);
            console.log('📧 Email:', user?.profile?.email);
            console.log('🆔 Subject:', user?.profile?.sub);
            console.log('🌍 Preferred Username:', user?.profile?.preferred_username);
            console.log('🔑 Roles:', user?.profile?.roles);
            console.log('🕐 Token expires at:', user?.expires_at ? new Date(user.expires_at * 1000).toISOString() : 'N/A');
            console.log('📦 Storage key will be:', `oidc.user:${window.location.origin}/oauth_callback`);
            console.groupEnd();
          },
          onUserUnloaded: () => {
            console.log(`🚪 [${new Date().toISOString()}] OIDC User Unloaded - User signed out`);
          },
          onAccessTokenExpiring: () => {
            console.warn(`⏰ [${new Date().toISOString()}] OIDC Access Token Expiring - Will attempt renewal`);
          },
          onAccessTokenExpired: () => {
            console.error(`💀 [${new Date().toISOString()}] OIDC Access Token Expired - Authentication required`);
          },
          onSilentRenewError: (error) => {
            console.error(`🔄 [${new Date().toISOString()}] OIDC Silent Renew Error:`, error);
          },
        };

        console.log('⚙️ Final OIDC config created');
        console.log('🔄 Automatic silent renew:', theConfig.automaticSilentRenew);
        console.log('📱 Response type:', theConfig.response_type);
        console.log('🎯 Scope:', theConfig.scope);
        
        setOidcConfig(theConfig);
        console.log('✅ OIDC configuration set successfully');
        console.groupEnd();
      } catch (error) {
        console.error(`💥 [${timestamp}] Error fetching OIDC config:`, error);
        console.error('🔍 Error details:');
        console.error('   Message:', error.message);
        console.error('   Stack:', error.stack);
        console.error('🎯 Check:');
        console.error('   1. OIDC provider URL is accessible');
        console.error('   2. Network connectivity');
        console.error('   3. CORS configuration');
        console.error('   4. Environment variables are set correctly');
        console.groupEnd();
      }
    };

    fetchOidcConfig();
  }, []);

  if (!oidcConfig) {
    return <div>Loading OIDC configuration...</div>; // Loading state while config is fetched
  }

  return (
      <>
        <AuthProvider
            {...oidcConfig}
            onSigninCallback={(user) => {
              const timestamp = new Date().toISOString();
              console.group(`🎉 [${timestamp}] AuthProvider Signin Callback`);
              console.log('👤 User received in callback:', user?.profile?.email || user?.profile?.sub);
              console.log('🎫 Access token in callback:', user?.access_token ? 'PRESENT' : 'MISSING');
              console.log('📍 Current location search:', location.search);
              console.log('🧭 Navigating with replace: true');
              console.groupEnd();
              navigate(location.search, {replace: true});
            }}
        >
          <Toaster/>
          <UserSet/>
          <Routes>
            <Route path="/login" element={<Login/>}/>
            <Route path="/signup" element={<Signup/>}/>
            <Route path="/oauth_callback" element={<OAuthCallback/>}/>

            {/* Public Routes with Sidebar Layout */}
            <Route element={<SidebarLayout/>}>
              <Route path="/" element={<NewLandingPage/>}/>
              <Route path="/resources" element={<Resources/>}/>
              <Route path="/resources/storage/:id" element={<ResourceDetail/>}/>
              <Route path="/resources/compute/:id" element={<ResourceDetail/>}/>
              <Route path="/events" element={<Events/>}/>
              <Route path="/resources/datasets" element={<Datasets/>}/>
              <Route path="/resources/notebooks" element={<Notebooks/>}/>
              <Route path="/resources/repositories" element={<Repositories/>}/>
              <Route path="/resources/models" element={<Models/>}/>
              <Route path="/resources/models/new" element={<AddModelForm/>}/>
              <Route path="/resources/datasets/new" element={<AddDatasetForm/>}/>
              <Route path="/resources/datasets/:id" element={<DatasetDetail/>}/>
              <Route path="/resources/models/:id" element={<ModelDetail/>}/>
              <Route path="/resources/notebooks/:id" element={<NotebookDetail/>}/>
              <Route path="/resources/repositories/:id" element={<RepositoryDetail/>}/>
              <Route path="/resources/compute/new" element={<AddComputeResourceForm/>}/>
              <Route path="/resources/compute/:id/edit" element={<AddComputeResourceForm/>}/>
              <Route path="/resources/storage/new" element={<AddStorageResourceForm/>}/>
              <Route path="/resources/storage/:id/edit" element={<AddStorageResourceForm/>}/>
              <Route path="/resources/notebooks/new" element={<AddNotebookForm/>}/>
              <Route path="/resources/repositories/new" element={<AddRepositoryForm/>}/>
              <Route path="/catalog" element={<Catalog/>}/>
              <Route path="/search" element={<SearchResults/>}/>
            </Route>

            {/* Protected Routes with Sidebar Layout */}
            <Route
                element={<ProtectedComponent Component={SidebarLayout}/>}
            >
              <Route path="/resources/starred" element={<StarredResourcesPage/>}/>
              <Route path="/add" element={<Add/>}/>
              <Route path="/add/repo" element={<AddRepoMaster/>}/>
              <Route path="/add/project" element={<AddProjectMaster/>}/>
            </Route>
          </Routes>
        </AuthProvider>
      </>
  );
}

export default App;
