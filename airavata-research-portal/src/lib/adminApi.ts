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

import axios, { AxiosInstance } from 'axios';

// Admin API Server configuration
const ADMIN_API_BASE_URL = 'http://localhost:8080';

// Create axios instance for admin API
const adminApi: AxiosInstance = axios.create({
  baseURL: `${ADMIN_API_BASE_URL}/api`,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Response interceptor for error handling
adminApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Admin API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Admin API service functions
export const adminApiService = {
  // Health check endpoint
  async getHealth() {
    const response = await adminApi.get('/health');
    return response.data;
  },

  // Test data endpoint
  async getTestData() {
    const response = await adminApi.get('/test');
    return response.data;
  },

  // Models endpoints
  async getModels() {
    const response = await adminApi.get('/models');
    return response.data;
  },

  async getModelById(id: number) {
    const response = await adminApi.get(`/models/${id}`);
    return response.data;
  },

  async getModelsByCategory(category: string) {
    const response = await adminApi.get(`/models/category/${category}`);
    return response.data;
  },

  async searchModels(keyword: string) {
    const response = await adminApi.get(`/models/search?keyword=${encodeURIComponent(keyword)}`);
    return response.data;
  },

  async createModel(model: any) {
    const response = await adminApi.post('/models', model);
    return response.data;
  },

  async starModel(id: number) {
    const response = await adminApi.post(`/models/${id}/star`);
    return response.data;
  },

  // Datasets endpoints
  async getDatasets() {
    const response = await adminApi.get('/datasets');
    return response.data;
  },

  async getDatasetById(id: number) {
    const response = await adminApi.get(`/datasets/${id}`);
    return response.data;
  },

  async getDatasetsByCategory(category: string) {
    const response = await adminApi.get(`/datasets/category/${category}`);
    return response.data;
  },

  async searchDatasets(keyword: string) {
    const response = await adminApi.get(`/datasets/search?keyword=${encodeURIComponent(keyword)}`);
    return response.data;
  },

  async createDataset(dataset: any) {
    const response = await adminApi.post('/datasets', dataset);
    return response.data;
  },

  async starDataset(id: number) {
    const response = await adminApi.post(`/datasets/${id}/star`);
    return response.data;
  },

  // Notebooks endpoints
  async getNotebooks() {
    const response = await adminApi.get('/notebooks');
    return response.data;
  },

  async getNotebookById(id: number) {
    const response = await adminApi.get(`/notebooks/${id}`);
    return response.data;
  },

  async searchNotebooks(keyword: string) {
    const response = await adminApi.get(`/notebooks/search?keyword=${encodeURIComponent(keyword)}`);
    return response.data;
  },

  async createNotebook(notebook: any) {
    const response = await adminApi.post('/notebooks', notebook);
    return response.data;
  },

  async starNotebook(id: number) {
    const response = await adminApi.post(`/notebooks/${id}/star`);
    return response.data;
  },

  // Repositories endpoints
  async getRepositories() {
    const response = await adminApi.get('/repositories');
    return response.data;
  },

  async getRepositoryById(id: number) {
    const response = await adminApi.get(`/repositories/${id}`);
    return response.data;
  },

  async searchRepositories(keyword: string) {
    const response = await adminApi.get(`/repositories/search?keyword=${encodeURIComponent(keyword)}`);
    return response.data;
  },

  async createRepository(repository: any) {
    const response = await adminApi.post('/repositories', repository);
    return response.data;
  },

  async starRepository(id: number) {
    const response = await adminApi.post(`/repositories/${id}/star`);
    return response.data;
  },

  // Storage Resources endpoints
  async getStorageResources() {
    const response = await adminApi.get('/storage-resources');
    return response.data;
  },

  async getStorageResourceById(id: number) {
    const response = await adminApi.get(`/storage-resources/${id}`);
    return response.data;
  },

  async createStorageResource(storageResource: any) {
    const response = await adminApi.post('/storage-resources', storageResource);
    return response.data;
  },

  async searchStorageResources(keyword: string) {
    const response = await adminApi.get(`/storage-resources/search?keyword=${encodeURIComponent(keyword)}`);
    return response.data;
  },

  // Compute Resources endpoints
  async getComputeResources() {
    const response = await adminApi.get('/compute-resources');
    return response.data;
  },

  async getComputeResourceById(id: number) {
    const response = await adminApi.get(`/compute-resources/${id}`);
    return response.data;
  },

  async createComputeResource(computeResource: any) {
    const response = await adminApi.post('/compute-resources', computeResource);
    return response.data;
  },

  async searchComputeResources(keyword: string) {
    const response = await adminApi.get(`/compute-resources/search?keyword=${encodeURIComponent(keyword)}`);
    return response.data;
  },
};

export default adminApi;