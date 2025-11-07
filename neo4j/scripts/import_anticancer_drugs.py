"""
Neo4j Import Script: AnticancerDrug Nodes
- Import 154 anticancer drug ingredients as nodes
- Create indexes for fast lookup
- Validate import success
"""

import json
from pathlib import Path
from typing import List, Dict
import sys
import os

try:
    from neo4j import GraphDatabase
    from dotenv import load_dotenv
except ImportError as e:
    print(f"[ERROR] Required package not installed: {e}")
    print("Please install: pip install neo4j python-dotenv")
    sys.exit(1)

# Load environment variables
load_dotenv()


class Neo4jAnticancerImporter:
    """Import anticancer drug data into Neo4j"""

    def __init__(self, uri: str, user: str, password: str):
        """
        Initialize Neo4j connection

        Args:
            uri: Neo4j URI (default: bolt://localhost:7687)
            user: Username (default: neo4j)
            password: Your password
        """
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        print(f"[OK] Connected to Neo4j at {uri}")

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

    def clear_anticancer_data(self):
        """Clear existing AnticancerDrug nodes (optional)"""
        with self.driver.session() as session:
            result = session.run("MATCH (n:AnticancerDrug) DETACH DELETE n")
            print("[OK] Cleared existing AnticancerDrug nodes")

    def create_indexes(self):
        """Create indexes for fast lookup"""
        with self.driver.session() as session:
            # Create indexes
            indexes = [
                "CREATE INDEX anticancer_atc IF NOT EXISTS FOR (d:AnticancerDrug) ON (d.atc_code)",
                "CREATE INDEX anticancer_ingredient_ko IF NOT EXISTS FOR (d:AnticancerDrug) ON (d.ingredient_ko)",
                "CREATE INDEX anticancer_ingredient_en IF NOT EXISTS FOR (d:AnticancerDrug) ON (d.ingredient_en)",
                "CREATE INDEX anticancer_level1 IF NOT EXISTS FOR (d:AnticancerDrug) ON (d.atc_level1)",
                "CREATE INDEX anticancer_level2 IF NOT EXISTS FOR (d:AnticancerDrug) ON (d.atc_level2)",
                "CREATE INDEX anticancer_category IF NOT EXISTS FOR (d:AnticancerDrug) ON (d.therapeutic_category)"
            ]

            for idx_query in indexes:
                session.run(idx_query)

            print(f"[OK] Created {len(indexes)} indexes")

    def import_anticancer_drugs(self, data: List[Dict]) -> int:
        """
        Import anticancer drug nodes in batch

        Args:
            data: List of drug dictionaries

        Returns:
            Number of nodes created
        """
        cypher_query = """
        UNWIND $drugs AS drug
        CREATE (d:AnticancerDrug {
            atc_code: drug.atc_code,
            ingredient_ko: drug.ingredient_ko,
            ingredient_en: drug.ingredient_en,
            ingredient_ko_original: drug.ingredient_ko_original,

            ingredient_base_ko: drug.ingredient_base_ko,
            ingredient_base_en: drug.ingredient_base_en,
            ingredient_precise_ko: drug.ingredient_precise_ko,
            ingredient_precise_en: drug.ingredient_precise_en,
            salt_form: drug.salt_form,
            ingredient_source: drug.ingredient_source,
            is_recombinant: drug.is_recombinant,

            brand_names_clean: drug.brand_names_clean,
            brand_names_raw: drug.brand_names_raw,
            brand_name_primary: drug.brand_name_primary,
            brand_count: drug.brand_count,

            atc_level1: drug.atc_level1,
            atc_level1_name: drug.atc_level1_name,
            atc_level2: drug.atc_level2,
            atc_level2_name: drug.atc_level2_name,
            atc_level3: drug.atc_level3,
            atc_level3_name: drug.atc_level3_name,

            mechanism_of_action: drug.mechanism_of_action,
            therapeutic_category: drug.therapeutic_category,

            manufacturers: drug.manufacturers,
            product_codes: drug.product_codes,
            ingredient_code: drug.ingredient_code
        })
        RETURN count(d) as created_count
        """

        with self.driver.session() as session:
            result = session.run(cypher_query, drugs=data)
            record = result.single()
            created_count = record["created_count"] if record else 0

        return created_count

    def verify_import(self) -> Dict:
        """
        Verify imported data

        Returns:
            Statistics dictionary
        """
        with self.driver.session() as session:
            # Total count
            total_result = session.run("MATCH (d:AnticancerDrug) RETURN count(d) as total")
            total_count = total_result.single()["total"]

            # Count by ATC Level 1
            l1_result = session.run("""
                MATCH (d:AnticancerDrug)
                RETURN d.atc_level1 as level1, d.atc_level1_name as name, count(d) as count
                ORDER BY count DESC
            """)
            l1_distribution = [(r["level1"], r["name"], r["count"]) for r in l1_result]

            # Count by therapeutic category
            cat_result = session.run("""
                MATCH (d:AnticancerDrug)
                WHERE d.therapeutic_category IS NOT NULL
                RETURN d.therapeutic_category as category, count(d) as count
                ORDER BY count DESC
            """)
            category_distribution = [(r["category"], r["count"]) for r in cat_result]

            # Sample drugs
            sample_result = session.run("""
                MATCH (d:AnticancerDrug)
                RETURN d.ingredient_ko, d.atc_code, d.therapeutic_category
                LIMIT 5
            """)
            samples = [(r["d.ingredient_ko"], r["d.atc_code"], r["d.therapeutic_category"])
                      for r in sample_result]

        return {
            "total_count": total_count,
            "l1_distribution": l1_distribution,
            "category_distribution": category_distribution,
            "samples": samples
        }


def main():
    print("=" * 60)
    print("Neo4j Import: AnticancerDrug Nodes")
    print("=" * 60)

    # Load configuration from .env
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    if not NEO4J_PASSWORD:
        print("\n[ERROR] NEO4J_PASSWORD not found in .env file")
        print("Please add Neo4j configuration to .env file")
        sys.exit(1)

    # File path
    data_file = Path("C:/Jimin/scrape-hub/bridges/anticancer_master_classified.json")

    # Step 1: Load data
    print(f"\n[1/5] Loading data: {data_file.name}")
    if not data_file.exists():
        print(f"[ERROR] File not found: {data_file}")
        sys.exit(1)

    with open(data_file, 'r', encoding='utf-8') as f:
        drugs_data = json.load(f)

    print(f"   >> Loaded {len(drugs_data)} drugs")

    # Step 2: Connect to Neo4j
    print(f"\n[2/5] Connecting to Neo4j...")
    print(f"   URI: {NEO4J_URI}")
    print(f"   User: {NEO4J_USER}")

    try:
        importer = Neo4jAnticancerImporter(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    except Exception as e:
        print(f"[ERROR] Failed to connect to Neo4j: {e}")
        print("\nTroubleshooting:")
        print("  1. Check Neo4j is running (Neo4j Desktop → Start)")
        print("  2. Verify URI: bolt://localhost:7687")
        print("  3. Check username/password")
        print("  4. Update NEO4J_PASSWORD in this script")
        sys.exit(1)

    # Step 3: Clear existing data (optional)
    print(f"\n[3/5] Clearing existing AnticancerDrug nodes...")
    importer.clear_anticancer_data()

    # Step 4: Import drugs
    print(f"\n[4/5] Importing {len(drugs_data)} AnticancerDrug nodes...")
    created_count = importer.import_anticancer_drugs(drugs_data)
    print(f"   [OK] Created {created_count} nodes")

    # Step 5: Create indexes
    print(f"\n[5/5] Creating indexes...")
    importer.create_indexes()

    # Verify import
    print(f"\n[6/6] Verifying import...")
    stats = importer.verify_import()

    print(f"\n   Total nodes: {stats['total_count']}")
    print(f"\n   ATC Level 1 distribution:")
    for level, name, count in stats['l1_distribution']:
        print(f"      {level} ({name}): {count}")

    print(f"\n   Therapeutic category distribution:")
    for category, count in stats['category_distribution']:
        print(f"      {category}: {count}")

    print(f"\n   Sample drugs:")
    for ko_name, atc, category in stats['samples']:
        print(f"      {ko_name} ({atc}) - {category}")

    # Close connection
    importer.close()

    # Summary
    print("\n" + "=" * 60)
    print("[SUCCESS] Import Complete")
    print("=" * 60)
    print(f"\n Imported: {created_count} AnticancerDrug nodes")
    print(f" Indexes: 6 created")
    print(f"\nNext steps:")
    print(f"  1. Open Neo4j Browser: http://localhost:7474")
    print(f"  2. Run query: MATCH (d:AnticancerDrug) RETURN d LIMIT 25")
    print(f"  3. Explore the graph!")


if __name__ == '__main__':
    main()
