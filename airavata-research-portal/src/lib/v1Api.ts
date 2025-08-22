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

import axios from 'axios';
import { CLIENT_ID } from './constants';

const v1Api = axios.create({
  baseURL: 'http://localhost:8080/api/v1/rf',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication - JWT ONLY
v1Api.interceptors.request.use(
  (config) => {
    const timestamp = new Date().toISOString();
    console.group(`🔐 [${timestamp}] v1Api Authentication Check`);
    console.log('📡 Request URL:', config.url);
    console.log('🎯 Request Method:', config.method?.toUpperCase());
    console.log('🏠 Window Origin:', window.location.origin);
    
    // JWT authentication - NO FALLBACK
    try {
      // Correct OIDC localStorage key format: oidc.user:<authority>:<client_id>
      const oidcStorageKey = `oidc.user:https://auth.dev.cybershuttle.org/realms/default:${CLIENT_ID}`;
      console.log('🔍 OIDC Key:', oidcStorageKey);
      
      // Show ALL localStorage keys for debugging
      console.log('🗄️ localStorage keys:', Object.keys(localStorage));
      
      const oidcStorage = localStorage.getItem(oidcStorageKey);
      console.log('📦 OIDC storage found:', !!oidcStorage);
      
      if (oidcStorage) {
        console.log('✅ OIDC storage found, parsing...');
        try {
          const user = JSON.parse(oidcStorage);
          console.log('👤 User object keys:', Object.keys(user || {}));
          console.log('🕐 Token expires at:', user?.expires_at ? new Date(user.expires_at * 1000).toISOString() : 'N/A');
          console.log('🕐 Current time:', new Date().toISOString());
          
          if (user && user.access_token) {
            const tokenPreview = user.access_token.substring(0, 20) + '...';
            const tokenLength = user.access_token.length;
            console.log('🎫 JWT token found:', tokenPreview);
            console.log('📏 Token length:', tokenLength);
            console.log('👤 User email:', user.profile?.email || 'N/A');
            console.log('🆔 User subject:', user.profile?.sub || 'N/A');
            console.log('🌍 User preferred_username:', user.profile?.preferred_username || 'N/A');
            console.log('🔑 User roles:', user.profile?.roles || 'N/A');
            
            // Check if token is expired
            if (user.expires_at && user.expires_at < Date.now() / 1000) {
              console.error('💀 JWT token is EXPIRED!');
              console.log('⏰ Token expired at:', new Date(user.expires_at * 1000).toISOString());
              console.log('⏰ Current time:', new Date().toISOString());
            } else {
              console.log('✅ JWT token is valid (not expired)');
            }
            
            // Set authorization headers
            config.headers.Authorization = `Bearer ${user.access_token}`;
            
            const claims = {
              "userName": user.profile?.email || user.profile?.sub || user.profile?.preferred_username,
              "gatewayID": "default",
            };
            config.headers["X-Claims"] = JSON.stringify(claims);
            
            console.log('✨ Authentication Method: JWT TOKEN ONLY');
            console.log('📤 Authorization Header:', `Bearer ${tokenPreview}`);
            console.log('📤 X-Claims Header:', claims);
            console.log('✅ Request authenticated successfully');
            console.groupEnd();
            return config;
          } else {
            console.error('❌ No access_token found in user object');
            console.log('🔍 User object structure:', JSON.stringify(user, null, 2));
          }
        } catch (parseError) {
          console.error('💥 Failed to parse OIDC storage JSON:', parseError);
          console.log('📄 Raw OIDC storage:', oidcStorage.substring(0, 200) + '...');
        }
      } else {
        console.error('❌ No OIDC storage found');
      }
    } catch (error) {
      console.error('💥 JWT token processing error:', error);
    }
    
    console.error('🚫 NO AUTHENTICATION - Request will fail with 401');
    
    console.groupEnd();
    return config;
  },
  (error) => {
    const timestamp = new Date().toISOString();
    console.error(`🔥 [${timestamp}] v1Api request interceptor error:`, error);
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors with detailed logging
v1Api.interceptors.response.use(
  (response) => {
    const timestamp = new Date().toISOString();
    console.group(`✅ [${timestamp}] v1Api Response Success`);
    console.log('📡 URL:', response.config?.url);
    console.log('🎯 Method:', response.config?.method?.toUpperCase());
    console.log('📊 Status:', response.status);
    console.log('📋 Status Text:', response.statusText);
    console.log('📦 Data Type:', typeof response.data);
    console.log('📏 Data Length:', Array.isArray(response.data) ? response.data.length : 'N/A');
    console.groupEnd();
    return response;
  },
  (error) => {
    const timestamp = new Date().toISOString();
    console.group(`❌ [${timestamp}] v1Api Response Error`);
    console.error('🔥 Error Details:', error);
    console.log('📡 URL:', error.config?.url);
    console.log('🎯 Method:', error.config?.method?.toUpperCase());
    console.log('📊 Status:', error.response?.status);
    console.log('📋 Status Text:', error.response?.statusText);
    console.log('💬 Error Message:', error.message);
    
    if (error.response) {
      console.log('📦 Response Data:', error.response.data);
      console.log('📋 Response Headers:', error.response.headers);
      
      // Authentication-specific error analysis
      if (error.response.status === 401) {
        console.error('🚫 AUTHENTICATION FAILED (401)');
        console.error('💡 Possible causes:');
        console.error('   1. JWT token is missing or invalid');
        console.error('   2. Token has expired');
        console.error('   3. OIDC configuration is incorrect');
        console.error('   4. Backend JWT validation failed');
      } else if (error.response.status === 403) {
        console.error('🚫 AUTHORIZATION FAILED (403)');
        console.error('💡 User is authenticated but lacks permissions');
      } else if (error.response.status >= 500) {
        console.error('💥 SERVER ERROR (5xx)');
        console.error('💡 Backend service may be down or misconfigured');
      }
    } else if (error.request) {
      console.error('📡 Network Error - No Response Received');
      console.error('🌐 Request was made but no response received');
      console.error('💡 Possible causes:');
      console.error('   1. Backend service is not running');
      console.error('   2. Network connectivity issues');
      console.error('   3. CORS configuration problems');
    } else {
      console.error('⚙️ Request Setup Error');
      console.error('💡 Error occurred while setting up the request');
    }
    
    console.groupEnd();
    return Promise.reject(error);
  }
);

export const v1ApiService = {
  // Dataset endpoints using v1 API
  async getDatasets(pageNumber = 0, pageSize = 50, nameSearch = '') {
    const params = new URLSearchParams({
      pageNumber: pageNumber.toString(),
      pageSize: pageSize.toString(),
      nameSearch: nameSearch,
      type: 'DATASET'
    });
    
    const response = await v1Api.get(`/resources/public?${params}`);
    return response.data;
  },

  async getDatasetById(id: string) {
    const response = await v1Api.get(`/resources/public/${id}`);
    return response.data;
  },

  async searchDatasets(keyword: string) {
    const response = await v1Api.get(`/resources/search?type=DATASET&name=${encodeURIComponent(keyword)}`);
    return response.data;
  },

  async createDataset(dataset: any) {
    const response = await v1Api.post('/resources/dataset', dataset);
    return response.data;
  },

  async deleteDataset(id: string) {
    const response = await v1Api.delete(`/resources/${id}`);
    return response.data;
  },

  // Star endpoints - using actual v1 API endpoints
  async starDataset(id: string) {
    const response = await v1Api.post(`/resources/${id}/star`);
    return response.data; // Returns boolean indicating new star state
  },

  async getDatasetStarStatus(id: string) {
    const response = await v1Api.get(`/resources/${id}/star`);
    return response.data; // Returns boolean indicating if starred
  },

  // Tags endpoint
  async getAllTags() {
    const response = await v1Api.get('/resources/public/tags/all');
    return response.data;
  },

  // Get starred resources - requires user ID
  async getStarredResources(userId: string) {
    const response = await v1Api.get(`/resources/${userId}/stars`);
    return response.data; // Returns List<Resource>
  },

  // Model endpoints using v1 API
  async getModels(pageNumber = 0, pageSize = 50, nameSearch = '') {
    const params = new URLSearchParams({
      pageNumber: pageNumber.toString(),
      pageSize: pageSize.toString(),
      nameSearch: nameSearch,
      type: 'MODEL'
    });
    
    const response = await v1Api.get(`/resources/public?${params}`);
    return response.data;
  },

  async getModelById(id: string) {
    const response = await v1Api.get(`/resources/public/${id}`);
    return response.data;
  },

  async searchModels(keyword: string) {
    const response = await v1Api.get(`/resources/search?type=MODEL&name=${encodeURIComponent(keyword)}`);
    return response.data;
  },

  // Repository endpoints using v1 API
  async getRepositories(pageNumber = 0, pageSize = 50, nameSearch = '') {
    const params = new URLSearchParams({
      pageNumber: pageNumber.toString(),
      pageSize: pageSize.toString(),
      nameSearch: nameSearch,
      type: 'REPOSITORY'
    });
    
    const response = await v1Api.get(`/resources/public?${params}`);
    return response.data;
  },

  async getRepositoryById(id: string) {
    const response = await v1Api.get(`/resources/public/${id}`);
    return response.data;
  },

  async searchRepositories(keyword: string) {
    const response = await v1Api.get(`/resources/search?type=REPOSITORY&name=${encodeURIComponent(keyword)}`);
    return response.data;
  },

  // Notebook endpoints using v1 API
  async getNotebooks(pageNumber = 0, pageSize = 50, nameSearch = '') {
    const params = new URLSearchParams({
      pageNumber: pageNumber.toString(),
      pageSize: pageSize.toString(),
      nameSearch: nameSearch,
      type: 'NOTEBOOK'
    });
    
    const response = await v1Api.get(`/resources/public?${params}`);
    return response.data;
  },

  async getNotebookById(id: string) {
    const response = await v1Api.get(`/resources/public/${id}`);
    return response.data;
  },

  async searchNotebooks(keyword: string) {
    const response = await v1Api.get(`/resources/search?type=NOTEBOOK&name=${encodeURIComponent(keyword)}`);
    return response.data;
  }
};