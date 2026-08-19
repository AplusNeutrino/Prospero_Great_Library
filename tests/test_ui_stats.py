from pgl.history.stats import build_stats


def item(item_id, category, status, rating=None, playtime=0, recent=0, updated='2026-08-18T00:00:00Z'):
    return {
        'id': item_id,
        'category': category,
        'title': item_id,
        'status': status,
        'rating': {'normalized_10': rating} if rating is not None else None,
        'telemetry': {'steam': {'playtime_minutes': playtime, 'recent_playtime_minutes': recent, 'last_played_at': updated}} if category == 'game' else {},
        'timestamps': {'canonical_updated_at': updated},
    }


def test_navigation_counts_only_public_default_and_wishlist_buckets():
    public = [
        item('g1', 'game', 'completed', 8),
        item('g2', 'game', 'in_progress', 9),
        item('g3', 'game', 'wishlist'),
        item('g4', 'game', 'on_hold'),
        item('a1', 'anime', 'dropped'),
    ]
    stats = build_stats(public)
    nav = stats['navigation']
    assert nav['default_by_category']['game'] == 2
    assert nav['default_total'] == 2
    assert nav['wishlist_by_category']['game'] == 1
    assert nav['wishlist_total'] == 1
    assert nav['other_status_by_category']['on_hold']['game'] == 1
    assert nav['other_status_by_category']['dropped']['anime'] == 1


def test_rating_curve_excludes_unrated_wishlist_and_hidden_browse_states():
    public = [
        item('a', 'game', 'completed', 8.0),
        item('b', 'game', 'in_progress', 8.5),
        item('c', 'game', 'wishlist', 9.0),
        item('d', 'game', 'on_hold', 7.0),
        item('e', 'game', 'completed', None),
    ]
    stats = build_stats(public)
    curve = stats['rating_curve_distribution']
    idx8 = curve['bins'].index(8.0)
    idx9 = curve['bins'].index(9)
    assert curve['scopes']['all'][idx8] == 1
    assert curve['scopes']['game'][idx9] == 1  # 8.5 folds to integer 9
    # Wishlist 9.0 remains excluded; only the in-progress 8.5 contributes here.
    assert curve['scopes']['all'][idx9] == 1
    assert sum(curve['scopes']['all']) == 2


def test_current_activity_includes_all_in_progress_and_recent_only_game_once():
    public = [
        item('progress', 'anime', 'in_progress', 8),
        item('both', 'game', 'in_progress', 9, playtime=600, recent=120),
        item('recent-only', 'game', 'completed', 8, playtime=900, recent=180),
        item('old', 'game', 'completed', 8, playtime=100, recent=0),
    ]
    rows = build_stats(public)['current_activity']
    assert [row['entity_id'] for row in rows].count('both') == 1
    assert {row['entity_id'] for row in rows} == {'progress', 'both', 'recent-only'}
    assert [row['reason'] for row in rows[:2]] == ['in_progress', 'in_progress']
    recent = next(row for row in rows if row['entity_id'] == 'recent-only')
    assert recent['reason'] == 'steam_recent'


def test_stats_only_item_may_aggregate_but_never_enters_identity_navigation_or_ranking():
    visible = [item('public', 'game', 'completed', 8, playtime=60)]
    stats_only = item('secret-stats-only-title', 'game', 'completed', 9, playtime=120)
    stats = build_stats(visible, aggregate_items=[*visible, stats_only])
    assert stats['total_items'] == 2
    assert stats['steam']['lifetime_playtime_minutes'] == 180
    assert stats['navigation']['default_by_category']['game'] == 1
    assert all(row['id'] != 'secret-stats-only-title' for row in stats['steam']['ranking'])
    assert all(row['entity_id'] != 'secret-stats-only-title' for row in stats['current_activity'])


def test_rating_curve_uses_integer_observation_bins_only():
    public = [item('x', 'movie', 'completed', 8.4), item('y', 'movie', 'completed', 8.5)]
    curve = build_stats(public)['rating_curve_distribution']
    assert curve['bins'] == list(range(1, 11))
    assert curve['bin_size'] == 1
    assert curve['scopes']['movie'][7] == 1  # 8.4 -> 8
    assert curve['scopes']['movie'][8] == 1  # 8.5 -> 9 (half-up)


def test_current_activity_primary_order_is_library_category_order():
    public = [
        item('game', 'game', 'in_progress', 8, updated='2026-08-19T09:00:00Z'),
        item('anime', 'anime', 'in_progress', 8, updated='2026-08-19T08:00:00Z'),
        item('book', 'book', 'in_progress', 8, updated='2026-08-18T01:00:00Z'),
        item('movie', 'movie', 'in_progress', 8, updated='2026-08-19T10:00:00Z'),
        item('comic', 'comic', 'in_progress', 8, updated='2026-08-19T11:00:00Z'),
        item('drama', 'drama', 'in_progress', 8, updated='2026-08-19T12:00:00Z'),
        item('music', 'music', 'in_progress', 8, updated='2026-08-19T13:00:00Z'),
    ]
    rows = build_stats(public)['current_activity']
    assert [row['category'] for row in rows] == ['book', 'comic', 'movie', 'drama', 'anime', 'game', 'music']
