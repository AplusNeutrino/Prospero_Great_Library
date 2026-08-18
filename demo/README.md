# PGL demo

This demo contains **fake fixture data only**. It is designed to exercise the V1 architecture contract without personal credentials.

Coverage includes all seven canonical categories, all five subjective statuses, Bangumi-only / NeoDB-only / Steam-only records, a Bangumi+NeoDB anime-film merge, Bangumi+Steam game telemetry merge, a performance-tag Movie, Book-vs-Comic separation, article associations, timeline events, and observed Steam playtime deltas.

Rebuild the generated demo data from the project root:

```bash
python demo/build_demo.py
```

The script intentionally runs two fixture syncs. The first uses lower synthetic Steam telemetry; the second uses the final fixtures so the demo history contains positive observed playtime and achievement changes.
