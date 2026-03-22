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

    // If DB was unavailable the categories have null IDs (fallback mode).
    // Don't mark the cache as loaded so the next navigation triggers a fresh
    // reload once the DB is ready.
    if (catData.fallback) return _cache;

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

/** Root-level values for a category (parent_id is null/undefined). */
export const getCacheRoots = catId =>
  getCacheValues(catId).filter(v => !v.parent_id);

/** Direct children of a value (parent_id matches). */
export const getCacheChildren = parentId =>
  Object.values(_cache.values)
    .flat()
    .filter(v => String(v.parent_id) === String(parentId));

/** All descendants of a value (recursive). Returns flat array. */
export function getCacheDescendants(parentId) {
  const children = getCacheChildren(parentId);
  return children.flatMap(c => [c, ...getCacheDescendants(c.id)]);
}

/** True if a value has any children. */
export const hasChildren = valId =>
  Object.values(_cache.values).flat().some(v => String(v.parent_id) === String(valId));

/**
 * Build full path string for a value: "grandparent / parent / name".
 * catId is needed to scope the lookup.
 */
export function getValuePath(catId, valId) {
  const all = getCacheValues(catId);
  const byId = Object.fromEntries(all.map(v => [String(v.id), v]));
  const parts = [];
  let cur = byId[String(valId)];
  while (cur) {
    parts.unshift(cur.name);
    cur = cur.parent_id ? byId[String(cur.parent_id)] : null;
  }
  return parts.join(' / ');
}

/** Leaf values for a category (values that have no children). */
export function getCacheLeaves(catId) {
  const all = getCacheValues(catId);
  const parentIds = new Set(all.map(v => String(v.parent_id)).filter(Boolean));
  return all.filter(v => !parentIds.has(String(v.id)));
}

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
