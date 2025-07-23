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
              <Route path="/resources/storage/new" element={<AddStorageResourceForm/>}/>
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
