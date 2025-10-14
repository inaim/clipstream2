const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

// If real Supabase env vars are provided, try to use the real client.
// Otherwise export a lightweight in-memory mock that provides the
// minimal subset of the Supabase API used by the app. This allows
// the app to run locally without a Supabase backend for development.
import backendModule from '../../../src/lib/backendClient';

let supabase: any = null;

// If environment provides real Supabase credentials and you want to use the
// official client, set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY and
// install @supabase/supabase-js in the frontend. Otherwise the app will
// use a lightweight in-memory mock or the backend adapter when enabled.
if (supabaseUrl && supabaseAnonKey) {
	try {
		// Use a dynamic import to keep bundling conditional.
		// Note: in the browser environment this will be tree-shaken if unused.
		// eslint-disable-next-line @typescript-eslint/no-var-requires
		const { createClient } = require('@supabase/supabase-js');
		supabase = createClient(supabaseUrl, supabaseAnonKey);
	} catch (err) {
		// Fall back to mock or backend adapter below.
	}
}

if (!supabase) {
	// Simple in-memory DB used for local development without Supabase.
	type Row = Record<string, any>;

	const makeId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

	const db: Record<string, Row[]> = {
		profiles: [],
		videos: [],
		likes: [],
		follows: [],
		messages: [],
		// add more tables as needed
	};

	let currentSession: { user: { id: string; email?: string } } | null = null;

	class QueryBuilder {
		table: string;
		filters: Array<(row: Row) => boolean> = [];

		constructor(table: string) {
			this.table = table;
		}

		select(_cols?: string) {
			// ignore projection for simplicity
			return this;
		}

		eq(field: string, value: any) {
			this.filters.push((row) => row[field] === value);
			return this;
		}

		maybeSingle() {
			const rows = db[this.table] || [];
			const results = rows.filter((r) => this.filters.every((f) => f(r)));
			return Promise.resolve({ data: results[0] ?? null, error: null });
		}

		async insert(records: Row | Row[]) {
			const arr = Array.isArray(records) ? records : [records];
			const inserted = arr.map((r) => {
				const row = { id: r.id ?? makeId(), ...r };
				db[this.table] = db[this.table] || [];
				db[this.table].push(row);
				return row;
			});
			return { data: inserted, error: null };
		}

		async delete() {
			const rows = db[this.table] || [];
			const remaining = rows.filter((r) => !this.filters.every((f) => f(r)));
			const removed = rows.length - remaining.length;
			db[this.table] = remaining;
			return { data: { removed }, error: null };
		}
	}

	const storage = {
		from: (bucket: string) => ({
			upload: async (_path: string, _file: File | Blob) => {
				// pretend upload succeeds
				return { error: null };
			},
			getPublicUrl: (path: string) => {
				// return a fake public URL that points to a local path
				return { data: { publicUrl: `/mock-storage/${bucket}/${path}` } };
			},
		}),
	};

	const auth = {
		getSession: async () => ({ data: { session: currentSession } }),
		onAuthStateChange: (_cb: (event: string, session: any) => void) => {
			// Simple subscription that exposes unsubscribe
			const subscription = { unsubscribe: () => {} };
			return { data: { subscription } };
		},
			signUp: async ({ email, password: _password }: { email: string; password: string }) => {
			// create a user and profile
			const id = makeId();
			const user = { id, email };
			currentSession = { user };
			db.profiles = db.profiles || [];
			db.profiles.push({ id, username: email?.split('@')[0] ?? id, display_name: email, avatar_url: '', bio: '' });
			return { data: { user }, error: null };
		},
			signInWithPassword: async ({ email, password: _password }: { email: string; password: string }) => {
			// Accept any password for local mock
			const found = (db.profiles || []).find((p) => p.username === (email?.split('@')[0] ?? ''));
			const user = found ? { id: found.id, email } : { id: makeId(), email };
			currentSession = { user };
			return { data: { user }, error: null };
		},
		signOut: async () => {
			currentSession = null;
			return { error: null };
		},
	};

	// If developer prefers to use the demo backend for CRUD instead of Supabase,
	// enable VITE_USE_BACKEND=true in your .env and set VITE_BACKEND_URL.
	const useBackend = !!(import.meta as any).env?.VITE_USE_BACKEND;

			if (useBackend) {
				supabase = backendModule;
			} else {
		supabase = {
			from: (table: string) => new QueryBuilder(table),
			storage,
			auth,
			// expose db for debugging in dev
			__mockDb: db,
		};
	}

}

export { supabase };
