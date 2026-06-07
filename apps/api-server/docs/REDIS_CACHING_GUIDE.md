# Redis Caching Guide - PostGIS Phase 3

## Overview

This guide explains the Redis caching integration for the geo search system, which significantly improves performance and reduces database load.

## Cache Strategy

### Cache TTL (Time-To-Live)

| Operation | TTL | Reason |
|-----------|-----|--------|
| Nearby search | 15 minutes | Location data changes infrequently |
| Full-text search | 10 minutes | Store data changes moderately |
| Geocoding | 1 hour | Admin data rarely changes |
| Reverse geocoding | 1 hour | Admin data rarely changes |
| Categories | 1 hour | Categories rarely change |
| Brands | 1 hour | Brands rarely change |
| Autocomplete | 5 minutes | Needs to be fresher for UX |

### Cache Keys

Cache keys follow the pattern: `prefix:param1:param2:...`

Examples:
- `nearby:10.7769:106.7009:5:cafe:circle-k`
- `search:Circle K:10.7769:106.7009:50:None:None`
- `geocode:nguyễn huệ, quận 1`
- `reverse_geocode:10.7769:106.7009`
- `categories`
- `brands:cafe`
- `autocomplete:ca:10.7769:106.7009`

## Implementation

### GeoCacheService

The `GeoCacheService` class in `src/services/geo_cache.py` provides:

- **Cache operations**: get/set for all geo operations
- **Pattern invalidation**: Invalidate keys matching a pattern
- **Flush all**: Clear entire cache
- **Statistics**: Get cache stats

### Integration with GeoSearchService

The `GeoSearchService` now includes caching:

```python
# Before database query
cached = await self.cache.get_search(query, lat, lng, ...)
if cached:
    return cached

# After database query
await self.cache.set_search(query, lat, lng, ..., result)
return result
```

## API Endpoints

### Cache Statistics

```http
GET /api/geo/cache/stats
```

Returns:
```json
{
  "enabled": true,
  "keyspace": "15.5M",
  "connected": true
}
```

### Invalidate Cache Pattern

```http
POST /api/geo/cache/invalidate?pattern=nearby:*
```

Invalidates all cache keys matching the pattern.

### Flush All Cache

```http
POST /api/geo/cache/flush
```

Clears all cache keys (use with caution).

## Performance Impact

### Before Caching

- Nearby search: 5-10ms (database query)
- Full-text search: 20-50ms (database query)
- Geocoding: 15-30ms (database query)
- Categories: 10-20ms (database query)

### After Caching

- Nearby search: < 1ms (cache hit)
- Full-text search: < 1ms (cache hit)
- Geocoding: < 1ms (cache hit)
- Categories: < 1ms (cache hit)

### Cache Hit Rate

Expected cache hit rates:
- Nearby search: 60-80% (popular locations)
- Full-text search: 40-60% (popular queries)
- Geocoding: 70-90% (common addresses)
- Categories: 95%+ (rarely changes)
- Brands: 95%+ (rarely changes)

## Cache Invalidation

### Automatic Invalidation

Cache entries expire automatically based on TTL:
- Nearby/search: 10-15 minutes
- Geocoding: 1 hour
- Categories/brands: 1 hour

### Manual Invalidation

When data is updated (e.g., new store added), invalidate relevant cache:

```python
# Invalidate all nearby cache
await geo_cache.invalidate_pattern("nearby:*")

# Invalidate all search cache
await geo_cache.invalidate_pattern("search:*")

# Invalidate specific category cache
await geo_cache.invalidate_pattern("brands:cafe")
```

### Data Update Triggers

Implement cache invalidation in data update endpoints:

```python
@router.post("/stores")
async def create_store(store_data: StoreCreate):
    # Create store
    store = await create_store(store_data)
    
    # Invalidate relevant cache
    await geo_cache.invalidate_pattern("nearby:*")
    await geo_cache.invalidate_pattern("search:*")
    await geo_cache.invalidate_pattern("autocomplete:*")
    
    return store
```

## Monitoring

### Cache Hit Rate

Monitor cache hit rate to ensure effectiveness:

```python
# Add logging to track hits/misses
logger.info(f"Cache HIT: search {query}")
logger.info(f"Cache MISS: search {query}")
```

### Cache Size

Monitor cache size to prevent memory issues:

```python
stats = await geo_cache.get_stats()
logger.info(f"Cache size: {stats['keyspace']}")
```

### Redis Metrics

Use Redis INFO command to get detailed metrics:

```bash
redis-cli INFO stats
redis-cli INFO memory
```

## Configuration

### Redis Connection

Configure Redis in `.env`:

```env
REDIS_URL=redis://localhost:6379/0
REDIS_MAX_CONNECTIONS=50
REDIS_SOCKET_TIMEOUT=5.0
```

### Cache TTL Adjustment

Adjust TTL in `src/services/geo_cache.py`:

```python
TTL_NEARBY = 15 * 60  # Increase to 30 minutes for more static data
TTL_SEARCH = 10 * 60  # Decrease to 5 minutes for more dynamic data
```

## Troubleshooting

### Cache Not Working

**Symptom**: Cache hits not occurring

**Solutions**:
1. Check Redis is running: `redis-cli ping`
2. Check Redis connection in logs
3. Verify cache service is enabled: `geo_cache.enabled`
4. Check for errors in cache operations

### High Memory Usage

**Symptom**: Redis using too much memory

**Solutions**:
1. Reduce TTL values
2. Implement cache eviction policy: `maxmemory-policy allkeys-lru`
3. Monitor cache size regularly
4. Flush cache if needed

### Stale Data

**Symptom**: Cached data is outdated

**Solutions**:
1. Reduce TTL for frequently changing data
2. Implement manual invalidation on data updates
3. Use cache versioning
4. Flush cache after major data imports

## Best Practices

1. **Cache frequently accessed data**: Categories, brands, popular searches
2. **Set appropriate TTL**: Balance freshness vs performance
3. **Invalidate on updates**: Clear cache when data changes
4. **Monitor hit rates**: Ensure cache is effective
5. **Handle cache failures**: Graceful degradation if Redis is down
6. **Use cache warming**: Pre-populate cache with common queries
7. **Implement cache versioning**: Handle schema changes
8. **Document cache keys**: Understand what's cached

## Testing

### Unit Tests

Test cache service independently:

```python
async def test_cache_set_get():
    cache = GeoCacheService()
    await cache.set_geocode("Test Address", {"lat": 10, "lng": 106})
    result = await cache.get_geocode("Test Address")
    assert result == {"lat": 10, "lng": 106}
```

### Integration Tests

Test cache with real Redis:

```python
async def test_cache_integration():
    # Test with actual Redis instance
    cache = GeoCacheService()
    assert cache.enabled is True
```

### Performance Tests

Measure cache impact:

```python
async def test_cache_performance():
    # Measure time with cache
    start = time.time()
    result = await geo_service.search("Circle K")
    cached_time = time.time() - start
    
    # Measure time without cache
    await geo_cache.flush_all()
    start = time.time()
    result = await geo_service.search("Circle K")
    uncached_time = time.time() - start
    
    assert cached_time < uncached_time
```

## References

- [Redis Documentation](https://redis.io/docs/)
- [Redis Caching Best Practices](https://redis.io/docs/manual/patterns/caching/)
- [Python Redis Client](https://redis.readthedocs.io/)
