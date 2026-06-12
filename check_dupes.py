import re
c = open('temp_frontend_repo/src/data/tools/categories.ts').read()
s = re.findall(r'slug: "([a-z0-9-]+)"', c)
d = [(x, s.count(x)) for x in set(s) if s.count(x) > 1]
print(f'Total entries: {len(s)}')
print(f'Unique slugs: {len(set(s))}')
if d:
    print(f'Duplicates: {d}')
else:
    print('No duplicate slugs')
