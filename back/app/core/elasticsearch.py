from elasticsearch import AsyncElasticsearch
from elasticsearch.helpers import async_bulk
from app.core.config import settings
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ElasticsearchManager:
    def __init__(self):
        self.client: Optional[AsyncElasticsearch] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Elasticsearch client."""
        es_config = {
            "hosts": [settings.ELASTICSEARCH_URL],
            "request_timeout": settings.ES_REQUEST_TIMEOUT,
            "max_retries": settings.ES_MAX_RETRIES,
            "retry_on_timeout": True,
        }
        
        if settings.ES_SECURITY_ENABLED:
            es_config["basic_auth"] = (settings.ES_USERNAME, settings.ES_PASSWORD)
        
        self.client = AsyncElasticsearch(**es_config)
    
    async def create_products_index(self):
        """Create products index with mappings."""
        index_name = settings.ES_INDEX_PRODUCTS
        
        mappings = {
            "properties": {
                "supplier_id": {"type": "keyword"},
                "supplier_name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword"}},
                },
                "supplier_inn": {"type": "keyword"},
                "sku": {
                    "type": "keyword",
                    "fields": {
                        "ngram": {
                            "type": "text",
                            "analyzer": "sku_analyzer",
                        }
                    },
                },
                "name": {
                    "type": "text",
                    "analyzer": "russian_analyzer",
                    "fields": {
                        "exact": {"type": "keyword"},
                        "suggest": {"type": "completion"},
                        "transliterated": {
                            "type": "text",
                            "analyzer": "transliteration_analyzer"
                        }
                    },
                },
                "brand": {
                    "type": "keyword",
                    "normalizer": "lowercase_normalizer",
                    "fields": {
                        "text": {
                            "type": "text",
                            "analyzer": "russian_analyzer"
                        }
                    }
                },
                "category": {
                    "type": "keyword",
                    "normalizer": "lowercase_normalizer",
                    "fields": {
                        "text": {
                            "type": "text",
                            "analyzer": "russian_analyzer"
                        }
                    }
                },
                "tags": {
                    "type": "text",
                    "analyzer": "russian_analyzer",
                    "fields": {
                        "keyword": {
                            "type": "keyword",
                            "normalizer": "lowercase_normalizer"
                        }
                    }
                },
                "price": {"type": "float"},
                "unit": {"type": "keyword"},
                "raw_text": {
                    "type": "text",
                    "analyzer": "russian_analyzer",
                },
                "last_updated": {"type": "date"},
            }
        }
        
        settings_config = {
            "number_of_shards": settings.ES_INDEX_SHARDS,
            "number_of_replicas": settings.ES_INDEX_REPLICAS,
            "refresh_interval": settings.ES_REFRESH_INTERVAL,
            "analysis": {
                "char_filter": {
                    "transliteration_map": {
                        "type": "mapping",
                        "mappings": [
                            "q=>й", "w=>ц", "e=>у", "r=>к", "t=>е", "y=>н", "u=>г",
                            "i=>ш", "o=>щ", "p=>з", "[=>х", "]=>ъ", "a=>ф", "s=>ы",
                            "d=>в", "f=>а", "g=>п", "h=>р", "j=>о", "k=>л", "l=>д",
                            ";=>ж", "'=>э", "z=>я", "x=>ч", "c=>с", "v=>м", "b=>и",
                            "n=>т", "m=>ь", ",=>б", ".=>ю",
                            "Q=>Й", "W=>Ц", "E=>У", "R=>К", "T=>Е", "Y=>Н", "U=>Г",
                            "I=>Ш", "O=>Щ", "P=>З", "{=>Х", "}=>Ъ", "A=>Ф", "S=>Ы",
                            "D=>В", "F=>А", "G=>П", "H=>Р", "J=>О", "K=>Л", "L=>Д",
                            ":=>Ж", "\"=>Э", "Z=>Я", "X=>Ч", "C=>С", "V=>М", "B=>И",
                            "N=>Т", "M=>Ь", "<=>Б", ">=>Ю"
                        ]
                    }
                },
                "analyzer": {
                    "russian_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "russian_stop",
                            "russian_stemmer",
                        ],
                    },
                    "sku_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "sku_ngram"],
                    },
                    "transliteration_analyzer": {
                        "type": "custom",
                        "char_filter": ["transliteration_map"],
                        "tokenizer": "standard",
                        "filter": [
                            "lowercase",
                            "russian_stop",
                            "russian_stemmer"
                        ]
                    }
                },
                "filter": {
                    "russian_stop": {
                        "type": "stop",
                        "stopwords": "_russian_",
                    },
                    "russian_stemmer": {
                        "type": "stemmer",
                        "language": "russian",
                    },
                    "sku_ngram": {
                        "type": "edge_ngram",
                        "min_gram": 3,
                        "max_gram": 15,
                    },
                },
                "normalizer": {
                    "lowercase_normalizer": {
                        "type": "custom",
                        "filter": ["lowercase"],
                    }
                },
            },
        }
        
        if await self.client.indices.exists(index=index_name):
            logger.info(f"Index {index_name} already exists")
            return
        
        await self.client.indices.create(
            index=index_name,
            mappings=mappings,
            settings=settings_config,
        )
        logger.info(f"Created index {index_name}")
    
    async def bulk_index_products(
        self, products: List[Dict[str, Any]], supplier_id: str
    ) -> Dict[str, int]:
        """Bulk index products to Elasticsearch."""
        actions = [
            {
                "_index": settings.ES_INDEX_PRODUCTS,
                "_id": f"{supplier_id}_{product.get('sku', '')}_{i}",
                "_source": product,
            }
            for i, product in enumerate(products)
        ]
        
        success, failed = await async_bulk(
            self.client,
            actions,
            chunk_size=settings.ES_BULK_SIZE,
            request_timeout=settings.ES_BULK_TIMEOUT,
        )
        
        logger.info(
            f"Indexed {success} products for supplier {supplier_id}, {failed} failed"
        )
        
        return {"success": success, "failed": failed}
    
    async def delete_supplier_products(self, supplier_id: str) -> int:
        """Delete all products for a supplier."""
        response = await self.client.delete_by_query(
            index=settings.ES_INDEX_PRODUCTS,
            body={"query": {"term": {"supplier_id": supplier_id}}},
        )
        
        deleted = response.get("deleted", 0)
        logger.info(f"Deleted {deleted} products for supplier {supplier_id}")
        return deleted
    
    async def search_products(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        size: int = 1000,
    ) -> Dict[str, Any]:
        """
        ИНТЕЛЛЕКТУАЛЬНЫЙ ПОИСК с максимальными возможностями:
        - Fuzzy matching (опечатки)
        - Стемминг (склонения и окончания)
        - Транслитерация (английская раскладка)
        - N-gram поиск по SKU
        - Wildcard для частичного совпадения
        - Phrase matching для точных фраз
        """
        
        should_clauses = [
            # 1. ТОЧНОЕ совпадение SKU (максимальный приоритет)
            {
                "term": {
                    "sku": {
                        "value": query.upper(),
                        "boost": settings.ES_SEARCH_BOOST_EXACT_SKU,
                    }
                }
            },
            
            # 2. N-GRAM поиск по SKU (частичное совпадение)
            {
                "match": {
                    "sku.ngram": {
                        "query": query,
                        "boost": settings.ES_SEARCH_BOOST_SKU_PARTIAL,
                    }
                }
            },
            
            # 3. БРЕНД - точное совпадение
            {
                "term": {
                    "brand": {
                        "value": query.lower(),
                        "boost": settings.ES_SEARCH_BOOST_BRAND,
                    }
                }
            },
            
            # 4. БРЕНД - с fuzzy (опечатки)
            {
                "match": {
                    "brand.text": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "boost": settings.ES_SEARCH_BOOST_BRAND * 0.8,
                    }
                }
            },
            
            # 5. НАЗВАНИЕ - с fuzzy и стеммингом
            {
                "match": {
                    "name": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "operator": "or",
                        "boost": settings.ES_SEARCH_BOOST_NAME,
                    }
                }
            },
            
            # 6. НАЗВАНИЕ - точная фраза (повышенный приоритет)
            {
                "match_phrase": {
                    "name": {
                        "query": query,
                        "boost": settings.ES_SEARCH_BOOST_NAME * 2,
                    }
                }
            },
            
            # 7. ТРАНСЛИТЕРАЦИЯ - английская раскладка -> русская
            {
                "match": {
                    "name.transliterated": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "boost": settings.ES_SEARCH_BOOST_NAME * 0.9,
                    }
                }
            },
            
            # 8. ТЕГИ - с стеммингом
            {
                "match": {
                    "tags": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "boost": settings.ES_SEARCH_BOOST_TAGS,
                    }
                }
            },
            
            # 9. КАТЕГОРИЯ - с fuzzy
            {
                "match": {
                    "category.text": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "boost": 2.0,
                    }
                }
            },
            
            # 10. WILDCARD поиск для частичного совпадения
            {
                "wildcard": {
                    "name": {
                        "value": f"*{query.lower()}*",
                        "boost": 1.0,
                    }
                }
            },
            
            # 11. RAW TEXT - полнотекстовый поиск
            {
                "match": {
                    "raw_text": {
                        "query": query,
                        "fuzziness": "AUTO",
                        "boost": 1.5,
                    }
                }
            },
        ]
        
        filter_clauses = []
        if filters:
            if filters.get("supplier_ids"):
                filter_clauses.append(
                    {"terms": {"supplier_id": filters["supplier_ids"]}}
                )
            if filters.get("brands"):
                filter_clauses.append(
                    {"terms": {"brand": [b.lower() for b in filters["brands"]]}}
                )
            if filters.get("categories"):
                filter_clauses.append(
                    {"terms": {"category": [c.lower() for c in filters["categories"]]}}
                )
            if filters.get("min_price") or filters.get("max_price"):
                price_range = {}
                if filters.get("min_price"):
                    price_range["gte"] = filters["min_price"]
                if filters.get("max_price"):
                    price_range["lte"] = filters["max_price"]
                filter_clauses.append({"range": {"price": price_range}})
        
        search_body = {
            "query": {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1,
                    "filter": filter_clauses if filter_clauses else [],
                }
            },
            "min_score": settings.ES_SEARCH_MIN_SCORE,
            "size": size,
        }
        
        response = await self.client.search(
            index=settings.ES_INDEX_PRODUCTS, body=search_body
        )
        
        return response
    
    async def close(self):
        """Close Elasticsearch connection."""
        if self.client:
            await self.client.close()


es_manager = ElasticsearchManager()
