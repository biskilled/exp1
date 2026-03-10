/**
 * tagCache.js — In-memory cache for entity categories + values.
 *
 * Loaded once per project open. Shared by the chat picker and Planner tab so
 * every navigation between them costs zero DB round-trips.
 *
 * Mutations update the cache synchronously; DB calls fire in the background.
 * Callers re-render from cache immediately, giving instant UI feedback.
 */

import { api } from './api.js';

let _cache = {
  project:    null,
  categories: [],   // [{id, name, color, icon, value_count}]
  values:     {},   // { "catId": [{id, name, description, status, event_count, due_date, ...}] }
  loaded:     false,
};

/** Load (or force-reload) all categories + their values for a project. */
export async function loadTagCache(project, force = false) {
  if (!force && _cache.project === project && _cache.loaded) return _cache;

  _cache = { project, categories: [], values: {}, loaded: false };
  try {
    const catData = await api.entities.listCategories(project);
    _cache.categories = catData.categories || [];

    // Load all categories' values in parallel — one batch instead of N serial calls
    await Promise.all(_cache.categories.map(async c => {
      try {
        const vData = await api.entities.listValues(project, c.id);
        _cache.values[String(c.id)] = vData.values || [];
        c.value_count = _cache.values[String(c.id)].length;
      } catch {
        _cache.values[String(c.id)] = [];
        c.value_count = 0;
      }
    }));

    _cache.loaded = true;
  } catch (e) {
    console.warn('[tagCache] load failed:', e.message);
  }
  return _cache;
}

export const getCache           = ()      => _cache;
export const getCacheCategories = ()      => _cache.categories;
export const getCacheValues     = catId   => _cache.values[String(catId)] || [];
export const getCacheProject    = ()      => _cache.project;
export const isCacheLoaded      = ()      => _cache.loaded;

/** Add a newly created value to the cache and bump the parent category count. */
export function addCachedValue(catId, value) {
  const key = String(catId);
  if (!_cache.values[key]) _cache.values[key] = [];
  _cache.values[key].push(value);
  const cat = _cache.categories.find(c => String(c.id) === key);
  if (cat) cat.value_count = _cache.values[key].length;
}

/** Shallow-patch a cached value by id (e.g. {status:'done'} or {description:'…'}). */
export function updateCachedValue(valId, patch) {
  for (const key of Object.keys(_cache.values)) {
    const idx = _cache.values[key].findIndex(v => v.id === valId);
    if (idx !== -1) {
      _cache.values[key][idx] = { ..._cache.values[key][idx], ...patch };
      return;
    }
  }
}

/** Remove a cached value by id and update the parent category count. */
export function removeCachedValue(valId) {
  for (const key of Object.keys(_cache.values)) {
    const idx = _cache.values[key].findIndex(v => v.id === valId);
    if (idx !== -1) {
      _cache.values[key].splice(idx, 1);
      const cat = _cache.categories.find(c => String(c.id) === key);
      if (cat) cat.value_count = _cache.values[key].length;
      return;
    }
  }
}

/** Add a newly created category to the cache. */
export function addCachedCategory(category) {
  _cache.categories.push({ ...category, value_count: 0 });
  _cache.values[String(category.id)] = [];
}
