"""
Test Neo4j connection
- Quick script to verify Neo4j is running and accessible
"""

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import sys

# Load environment variables
load_dotenv()


def test_connection(uri: str, user: str, password: str):
    """Test Neo4j connection"""
    try:
        print(f"Testing connection to Neo4j...")
        print(f"  URI: {uri}")
        print(f"  User: {user}")
        print()

        driver = GraphDatabase.driver(uri, auth=(user, password))

        # Test query
        with driver.session() as session:
            result = session.run("RETURN 'Connection successful!' as message")
            record = result.single()
            message = record["message"]

            print(f"[SUCCESS] {message}")

        # Get Neo4j version
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions")
            for record in result:
                name = record["name"]
                versions = record["versions"]
                print(f"  {name}: {versions[0]}")

        driver.close()
        print("\n[OK] Neo4j is ready!")
        return True

    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check Neo4j is running (Neo4j Desktop → Start button)")
        print("  2. Verify URI: bolt://localhost:7687")
        print("  3. Check username (default: neo4j)")
        print("  4. Check password (set during installation)")
        return False


if __name__ == '__main__':
    # Load configuration from .env
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    print("=" * 50)
    print("Neo4j Connection Test")
    print("=" * 50)
    print()

    if not NEO4J_PASSWORD:
        print("[ERROR] NEO4J_PASSWORD not found in .env file")
        print("Please add the following to .env:")
        print("  NEO4J_PASSWORD=your_password_here")
        sys.exit(1)

    print(f"Loaded from .env:")
    print(f"  URI: {NEO4J_URI}")
    print(f"  User: {NEO4J_USER}")
    print(f"  Password: {'*' * len(NEO4J_PASSWORD)}")
    print()

    success = test_connection(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    if success:
        print("\nYou're ready to run the import script!")
        print("  python scripts/neo4j/import_anticancer_drugs.py")
        sys.exit(0)
    else:
        sys.exit(1)
