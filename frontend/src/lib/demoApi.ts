// Compatibility wrapper for the frontend build.
// Re-export the ESM helpers from the repo-level implementation.
import { uploadViaBackend, getPlaybackUrl } from '../../../src/lib/demoApi';

export { uploadViaBackend, getPlaybackUrl };

const _default = { uploadViaBackend, getPlaybackUrl };
export default _default;
