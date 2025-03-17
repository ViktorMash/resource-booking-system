SELECT * FROM pg_catalog.pg_tables
WHERE schemaname = 'public';

SELECT * FROM alembic_version;


SELECT string_agg(
    format('SELECT %L AS table_name, COUNT(*) AS row_count FROM %I',
           tablename,
           tablename),
    ' UNION ALL '
) || ' ORDER BY table_name;' AS generated_query
FROM pg_catalog.pg_tables
WHERE schemaname = 'public'
AND tablename <> 'alembic_version';


SELECT 'resources' AS table_name, COUNT(*) AS row_count FROM resources UNION ALL SELECT 'bookings' AS table_name, COUNT(*) AS row_count FROM bookings UNION ALL SELECT 'users' AS table_name, COUNT(*) AS row_count FROM users UNION ALL SELECT 'groups' AS table_name, COUNT(*) AS row_count FROM groups UNION ALL SELECT 'permissions' AS table_name, COUNT(*) AS row_count FROM permissions UNION ALL SELECT 'user_group' AS table_name, COUNT(*) AS row_count FROM user_group ORDER BY table_name;


select * from rbs.public.users;
select * from rbs.public.bookings;


