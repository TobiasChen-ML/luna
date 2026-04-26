import { api } from '@/services/api';

export interface OpenPosePreset {
  id: string;
  name: string;
  image_url: string;
  is_active: boolean | number;
  created_at?: string;
  updated_at?: string;
}

export interface OpenPosePresetPayload {
  name: string;
  image_url: string;
  is_active: boolean;
}

export async function fetchOpenPosePresets(): Promise<OpenPosePreset[]> {
  const res = await api.get<{ poses: OpenPosePreset[] }>('/images/openpose-presets');
  return res.data.poses || [];
}

export async function fetchAdminOpenPosePresets(): Promise<OpenPosePreset[]> {
  const res = await api.get<{ poses: OpenPosePreset[] }>('/admin/openpose-presets');
  return res.data.poses || [];
}

export async function uploadOpenPoseImage(file: File): Promise<string> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await api.post<{ image_url: string }>('/admin/openpose-presets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data.image_url;
}

export async function createOpenPosePreset(payload: OpenPosePresetPayload): Promise<OpenPosePreset> {
  const res = await api.post<{ pose: OpenPosePreset }>('/admin/openpose-presets', payload);
  return res.data.pose;
}

export async function updateOpenPosePreset(
  id: string,
  payload: Partial<OpenPosePresetPayload>
): Promise<OpenPosePreset> {
  const res = await api.put<{ pose: OpenPosePreset }>(`/admin/openpose-presets/${id}`, payload);
  return res.data.pose;
}

export async function deleteOpenPosePreset(id: string): Promise<void> {
  await api.delete(`/admin/openpose-presets/${id}`);
}
