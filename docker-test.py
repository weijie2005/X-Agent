#!/usr/bin/env python3
'''
对docker-compose.yml安装的docker容器进行测试,期中参数配置在.env文件中

依赖安装:
pip install psycopg2-binary redis requests python-dotenv minio qdrant-client
'''

import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class DockerContainerTester:
    def __init__(self):
        self.results = {}
    
    def test_postgres(self):
        print("\n=== 测试 PostgreSQL 数据库 ===")
        try:
            import psycopg2
            
            pg_user = os.getenv('PG_USER', 'agentuser')
            pg_password = os.getenv('PG_PASSWORD', 'Agent@2026')
            pg_db = os.getenv('PG_DB', 'agent_db')
            pg_host = 'localhost'
            pg_port = 5432
            
            conn = psycopg2.connect(
                host=pg_host,
                port=pg_port,
                user=pg_user,
                password=pg_password,
                database=pg_db,
                connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            
            cursor.execute("SELECT current_database();")
            current_db = cursor.fetchone()[0]
            
            cursor.close()
            conn.close()
            
            print(f"✓ PostgreSQL 连接成功")
            print(f"  数据库版本: {version}")
            print(f"  当前数据库: {current_db}")
            self.results['postgres'] = True
            return True
            
        except ImportError:
            print("✗ 缺少依赖: psycopg2-binary")
            self.results['postgres'] = False
            return False
        except Exception as e:
            print(f"✗ PostgreSQL 连接失败: {e}")
            self.results['postgres'] = False
            return False
    
    def test_redis(self):
        print("\n=== 测试 Redis 缓存 ===")
        try:
            import redis
            
            redis_host = 'localhost'
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            client.ping()
            
            test_key = "test_key_docker_test"
            test_value = "test_value_12345"
            client.set(test_key, test_value, ex=10)
            retrieved_value = client.get(test_key)
            
            if retrieved_value == test_value:
                print(f"✓ Redis 连接成功")
                print(f"  主机: {redis_host}:{redis_port}")
                print(f"  读写测试: 通过")
                self.results['redis'] = True
                return True
            else:
                print(f"✗ Redis 读写测试失败")
                self.results['redis'] = False
                return False
                
        except ImportError:
            print("✗ 缺少依赖: redis")
            self.results['redis'] = False
            return False
        except Exception as e:
            print(f"✗ Redis 连接失败: {e}")
            self.results['redis'] = False
            return False
    
    def test_qdrant(self):
        print("\n=== 测试 Qdrant 向量数据库 ===")
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            qdrant_host = 'localhost'
            qdrant_port = int(os.getenv('QDRANT_PORT', 6333))
            
            client = QdrantClient(host=qdrant_host, port=qdrant_port)
            
            collections = client.get_collections()
            
            print(f"✓ Qdrant 连接成功")
            print(f"  主机: {qdrant_host}:{qdrant_port}")
            print(f"  现有集合数: {len(collections.collections)}")
            self.results['qdrant'] = True
            return True
            
        except ImportError:
            print("✗ 缺少依赖: qdrant-client")
            self.results['qdrant'] = False
            return False
        except Exception as e:
            print(f"✗ Qdrant 连接失败: {e}")
            self.results['qdrant'] = False
            return False
    
    def test_minio(self):
        print("\n=== 测试 MinIO 对象存储 ===")
        try:
            from minio import Minio
            from minio.error import S3Error
            
            minio_user = os.getenv('MINIO_ROOT_USER', 'admin')
            minio_password = os.getenv('MINIO_ROOT_PASSWORD', 'Minio@2026')
            minio_host = 'localhost:9000'
            
            client = Minio(
                minio_host,
                access_key=minio_user,
                secret_key=minio_password,
                secure=False
            )
            
            buckets = client.list_buckets()
            
            print(f"✓ MinIO 连接成功")
            print(f"  主机: {minio_host}")
            print(f"  现有桶数: {len(buckets)}")
            self.results['minio'] = True
            return True
            
        except ImportError:
            print("✗ 缺少依赖: minio")
            self.results['minio'] = False
            return False
        except Exception as e:
            print(f"✗ MinIO 连接失败: {e}")
            self.results['minio'] = False
            return False
    
    def test_loki(self):
        print("\n=== 测试 Loki 日志系统 ===")
        try:
            import requests
            
            loki_url = "http://localhost:3100/ready"
            
            response = requests.get(loki_url, timeout=5)
            
            if response.status_code == 200:
                print(f"✓ Loki 连接成功")
                print(f"  URL: http://localhost:3100")
                print(f"  状态: {response.text.strip()}")
                self.results['loki'] = True
                return True
            else:
                print(f"✗ Loki 返回异常状态码: {response.status_code}")
                self.results['loki'] = False
                return False
                
        except ImportError:
            print("✗ 缺少依赖: requests")
            self.results['loki'] = False
            return False
        except Exception as e:
            print(f"✗ Loki 连接失败: {e}")
            self.results['loki'] = False
            return False
    
    def test_playwright(self):
        print("\n=== 测试 Playwright 服务 ===")
        try:
            import requests
            
            playwright_url = "http://localhost:8050"
            
            try:
                response = requests.get(playwright_url, timeout=5)
                print(f"✓ Playwright 服务连接成功")
                print(f"  URL: {playwright_url}")
                print(f"  状态码: {response.status_code}")
                self.results['playwright'] = True
                return True
            except requests.exceptions.ConnectionError:
                print(f"⚠ Playwright 服务可能未配置HTTP服务")
                print(f"  容器运行中，但端口8050可能需要额外配置")
                print(f"  建议检查容器状态: docker ps | grep agent-playwright")
                self.results['playwright'] = False
                return False
                
        except ImportError:
            print("✗ 缺少依赖: requests")
            self.results['playwright'] = False
            return False
        except Exception as e:
            print(f"✗ Playwright 服务连接失败: {e}")
            self.results['playwright'] = False
            return False
        
    def test_docker_containers_status(self):
        print("\n=== 检查 Docker 容器状态 ===")
        try:
            import subprocess
            
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=agent-', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print(result.stdout)
                return True
            else:
                print(f"✗ Docker 命令执行失败: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("✗ Docker 未安装或不在PATH中")
            return False
        except Exception as e:
            print(f"✗ 检查容器状态失败: {e}")
            return False
    
    def run_all_tests(self):
        print("=" * 60)
        print("Docker 容器测试开始")
        print("=" * 60)
        
        self.test_docker_containers_status()
        
        self.test_postgres()
        self.test_redis()
        self.test_qdrant()
        self.test_minio()
        self.test_loki()
        self.test_playwright()        
        
        print("\n" + "=" * 60)
        print("测试结果汇总")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for v in self.results.values() if v)
        failed = total - passed
        
        for service, result in self.results.items():
            status = "✓ 通过" if result else "✗ 失败"
            print(f"{service:20s}: {status}")
        
        print(f"\n总计: {total} 个服务")
        print(f"通过: {passed} 个")
        print(f"失败: {failed} 个")
        
        if failed == 0:
            print("\n🎉 所有服务测试通过!")
            return 0
        else:
            print(f"\n⚠ 有 {failed} 个服务测试失败，请检查日志")
            return 1


def main():
    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        print("错误: .env 文件不存在")
        print(f"期望路径: {env_file}")
        sys.exit(1)
    
    tester = DockerContainerTester()
    exit_code = tester.run_all_tests()
    sys.exit(exit_code)


if __name__ == '__main__':
    main()