import axios, { AxiosInstance } from 'axios';
import { ComputeResource, BatchQueue, ResourceName } from '../interfaces/ComputeResourceType';
import { StorageResource } from '../interfaces/StorageResourceType';

const REST_API_URL = import.meta.env.VITE_REST_API_URL || 'http://localhost:8080';

const resourceApi: AxiosInstance = axios.create({
  baseURL: `${REST_API_URL}/api/v1`,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth if needed
resourceApi.interceptors.request.use(
  (config) => {
    // Add auth headers if available
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
resourceApi.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('Resource API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Compute Resource APIs
export const computeResourceApi = {
  getAll: async (): Promise<ResourceName[]> => {
    const response = await resourceApi.get('/compute-resources');
    return response.data;
  },

  get: async (id: string): Promise<ComputeResource> => {
    const response = await resourceApi.get(`/compute-resources/${id}`);
    return response.data;
  },

  create: async (resource: ComputeResource): Promise<{ computeResourceId: string }> => {
    const response = await resourceApi.post('/compute-resources', resource);
    return response.data;
  },

  update: async (id: string, resource: ComputeResource): Promise<void> => {
    await resourceApi.put(`/compute-resources/${id}`, resource);
  },

  delete: async (id: string): Promise<void> => {
    await resourceApi.delete(`/compute-resources/${id}`);
  },

  getQueues: async (id: string): Promise<BatchQueue[]> => {
    const response = await resourceApi.get(`/compute-resources/${id}/queues`);
    return response.data || [];
  },

  addQueue: async (id: string, queue: BatchQueue): Promise<void> => {
    await resourceApi.post(`/compute-resources/${id}/queues`, queue);
  },

  updateQueue: async (id: string, queueName: string, queue: BatchQueue): Promise<void> => {
    await resourceApi.put(`/compute-resources/${id}/queues/${queueName}`, queue);
  },

  deleteQueue: async (id: string, queueName: string): Promise<void> => {
    await resourceApi.delete(`/compute-resources/${id}/queues/${queueName}`);
  },
};

// Storage Resource APIs
export const storageResourceApi = {
  getAll: async (): Promise<ResourceName[]> => {
    const response = await resourceApi.get('/storage-resources');
    return response.data;
  },

  get: async (id: string): Promise<StorageResource> => {
    const response = await resourceApi.get(`/storage-resources/${id}`);
    return response.data;
  },

  create: async (resource: StorageResource): Promise<{ storageResourceId: string }> => {
    const response = await resourceApi.post('/storage-resources', resource);
    return response.data;
  },

  update: async (id: string, resource: StorageResource): Promise<void> => {
    await resourceApi.put(`/storage-resources/${id}`, resource);
  },

  delete: async (id: string): Promise<void> => {
    await resourceApi.delete(`/storage-resources/${id}`);
  },
};

export default resourceApi;



