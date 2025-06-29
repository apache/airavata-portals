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
import {Route, Routes, useLocation, useNavigate} from "react-router";
import Home from "./components/home";
import {Models} from "./components/models";
import {Datasets} from "./components/datasets";
import ResourceDetails from "./components/resources/ResourceDetails";
import Notebooks from "./components/notebooks";
import Repositories from "./components/repositories";
import {Login} from "./components/auth/UserLoginPage";
import ProtectedComponent from "./components/auth/ProtectedComponent";
import {AuthProvider, AuthProviderProps} from "react-oidc-context";
import {useEffect, useState} from "react";
import NavBarFooterLayout from "./layouts/NavBarFooterLayout";
import {CybershuttleLanding} from "./components/home/CybershuttleLanding";
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

function App() {
  const colorMode = useColorMode();
  const navigate = useNavigate();
  const location = useLocation();
  const [oidcConfig, setOidcConfig] = useState<AuthProviderProps | null>(null);

  if (colorMode.colorMode === "dark") {
    colorMode.toggleColorMode();
  }

  useEffect(() => {
    const fetchOidcConfig = async () => {
      try {
        const response = await fetch(OPENID_CONFIG_URL);
        const data = await response.json();

        const redirectUri = APP_REDIRECT_URI;

        const theConfig: AuthProviderProps = {
          authority: `https://auth.dev.cybershuttle.org/admin/master/console/#/default`,
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
        };

        setOidcConfig(theConfig);
      } catch (error) {
        console.error("Error fetching OIDC config:", error);
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
            onSigninCallback={() => {
              navigate(location.search, {replace: true});
            }}
        >
          <Toaster/>
          <UserSet/>
          <Routes>
            {/* Public Route */}
            <Route element={<NavBarFooterLayout/>}>
              <Route path="/" element={<CybershuttleLanding/>}/>
              <Route path="/login" element={<Login/>}/>
              <Route path="/resources" element={<Resources/>}/>
              <Route path="/events" element={<Events/>}/>
              <Route path="/resources/datasets" element={<Datasets/>}/>
              <Route path="/resources/notebooks" element={<Notebooks/>}/>
              <Route path="/resources/repositories" element={<Repositories/>}/>
              <Route path="/resources/models" element={<Models/>}/>
              <Route path="/resources/:type/:id" element={<ResourceDetails/>}/>
            </Route>

            {/* Protected Routes with Layout */}
            <Route
                element={<ProtectedComponent Component={NavBarFooterLayout}/>}
            >
              <Route path="/resources/starred" element={<StarredResourcesPage/>}/>
              <Route path="/sessions" element={<Home/>}/>
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
