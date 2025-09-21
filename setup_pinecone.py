#!/usr/bin/env python3
"""
Pinecone Setup Script
Creates the Pinecone index for vector search
"""

import os
import sys
from pinecone import Pinecone, ServerlessSpec

def setup_pinecone():
    """Setup Pinecone index for PartSelect vector search"""

    # Check for API key
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key or api_key == "your_pinecone_key_here":
        print("❌ Error: PINECONE_API_KEY not set or using placeholder value")
        print("Please set your Pinecone API key in the environment variables")
        print("Example: export PINECONE_API_KEY='your-actual-api-key'")
        return False

    index_name = os.getenv("PINECONE_INDEX_NAME", "partselect-parts")

    try:
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)

        # Check if index already exists
        existing_indexes = pc.list_indexes()
        if any(idx['name'] == index_name for idx in existing_indexes):
            print(f"✅ Index '{index_name}' already exists")
            return True

        print(f"🔄 Creating Pinecone index '{index_name}'...")

        # Create index with specifications for text-embedding-3-small
        pc.create_index(
            name=index_name,
            dimension=1536,  # text-embedding-3-small dimension
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )

        print(f"✅ Successfully created Pinecone index '{index_name}'")
        print("📝 Index specifications:")
        print("   - Dimension: 1536 (for text-embedding-3-small)")
        print("   - Metric: cosine")
        print("   - Cloud: AWS us-east-1 (serverless)")
        print("")
        print("🎉 Setup complete! You can now use vector search in the PartSelect chat agent.")
        return True

    except Exception as e:
        print(f"❌ Error setting up Pinecone: {e}")
        print("\nTroubleshooting tips:")
        print("1. Verify your PINECONE_API_KEY is correct")
        print("2. Check your Pinecone account has available quota")
        print("3. Make sure you have the pinecone-client package installed")
        return False

if __name__ == "__main__":
    print("🚀 PartSelect Pinecone Setup")
    print("=" * 40)

    success = setup_pinecone()

    if success:
        print("\n✅ Setup completed successfully!")
        print("You can now start the application with vector search enabled.")
    else:
        print("\n❌ Setup failed!")
        print("Vector search will not be available until this is resolved.")
        sys.exit(1)