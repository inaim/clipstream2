// Compatibility wrapper for the frontend build.
// Re-export the API helpers from the services module.
import { uploadViaBackend, getPlaybackUrl } from '../services/api';

export { uploadViaBackend, getPlaybackUrl };

const _default = { uploadViaBackend, getPlaybackUrl };
export default _default;
