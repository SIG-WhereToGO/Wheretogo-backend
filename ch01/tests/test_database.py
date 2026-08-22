#Session + Core/text of SQLAlchemy
from pgvector.sqlalchemy import Vector
from sqlalchemy import text, URL, create_engine
from sqlalchemy.orm import Session

url = URL.create(
    drivername="postgresql+psycopg2",
    username="neondb_owner",
    password="npg_axMZQ6C2KjRk",
    host="ep-small-water-az2ahrfi.c-3.ap-southeast-1.aws.neon.tech",
    database="KoTourism",
    query={"sslmode": "require"},
)

engine = create_engine(url)

query = text("""
            SELECT
                tst.spot_id AS spot_id,
                jsonb_object_agg(
                    t.name,
                    tst.confidence
                ) AS tourist_style_tags
            FROM "TouristSpotTag" tst
            JOIN "Tag" t
                ON tst.tag_id = t.tag_id
                AND t.category = 'style'
            GROUP BY tst.spot_id;
        """)



with Session(engine) as session:
    result = session.execute(query)
    row = result.first()

    print(row.spot_id)
    print(type(row.tourist_style_tags))
    print(row.tourist_style_tags)

    result = session.execute(
        query
    )

