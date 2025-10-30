"""
Test script pro eMISTR MCP Server
Testuje základní funkčnost bez spuštění plného MCP serveru
"""

import asyncio
import json
from database import DatabaseManager
from anonymizer import DataAnonymizer
from response_builder import ResponseBuilder
from config import Config


async def test_database_connection():
    """Test připojení k databázi"""
    print("🔌 Test připojení k databázi...")
    config = Config()
    db = DatabaseManager(config)
    
    try:
        await db.connect()
        print("✅ Připojení úspěšné")
        
        # Test jednoduchého dotazu
        result = await db.execute_query("SELECT VERSION()")
        print(f"✅ Verze MariaDB: {result[0] if result else 'N/A'}")
        
        await db.close()
        return True
    except Exception as e:
        print(f"❌ Chyba připojení: {e}")
        return False


async def test_get_orders():
    """Test načtení zakázek"""
    print("\n📋 Test načtení zakázek...")
    config = Config()
    db = DatabaseManager(config)
    anonymizer = DataAnonymizer(config)
    response_builder = ResponseBuilder()
    
    try:
        await db.connect()
        
        # Načtení zakázek
        result = await db.get_orders(status="ANO", limit=5)
        print(f"✅ Načteno {len(result.get('orders', []))} zakázek")
        
        # Anonymizace
        anonymized = anonymizer.anonymize_orders(result)
        print(f"✅ Data anonymizována")
        
        # Vytvoření odpovědi
        response = response_builder.build_orders_response(anonymized, {"status": "ANO"})
        print(f"✅ Response vytvořena")
        print(f"   Zpráva: {response.get('message')}")
        print(f"   Akce: {response.get('action', {}).get('type')}")
        
        # Výpis ukázky
        if result.get('orders'):
            first_order = anonymized['orders'][0]
            print(f"\n   Ukázka zakázky:")
            print(f"   - Kód: {first_order.get('code')}")
            print(f"   - Název: {first_order.get('name')}")
            print(f"   - Zákazník: {first_order.get('customer_name')}")
        
        await db.close()
        return True
    except Exception as e:
        print(f"❌ Chyba: {e}")
        return False


async def test_search_orders():
    """Test vyhledávání"""
    print("\n🔍 Test vyhledávání zakázek...")
    config = Config()
    db = DatabaseManager(config)
    
    try:
        await db.connect()
        
        result = await db.search_orders("2024", limit=5)
        print(f"✅ Nalezeno {result.get('count', 0)} zakázek")
        
        await db.close()
        return True
    except Exception as e:
        print(f"❌ Chyba: {e}")
        return False


async def test_get_workers():
    """Test načtení zaměstnanců"""
    print("\n👥 Test načtení zaměstnanců...")
    config = Config()
    db = DatabaseManager(config)
    anonymizer = DataAnonymizer(config)
    
    try:
        await db.connect()
        
        result = await db.get_workers(status="ANO", limit=5)
        print(f"✅ Načteno {len(result.get('workers', []))} zaměstnanců")
        
        # Anonymizace
        anonymized = anonymizer.anonymize_workers(result)
        
        if anonymized.get('workers'):
            first_worker = anonymized['workers'][0]
            print(f"\n   Ukázka zaměstnance:")
            print(f"   - ID: {first_worker.get('bar_id')}")
            print(f"   - Jméno: {first_worker.get('name')}")
            print(f"   - Email: {first_worker.get('email')}")
        
        await db.close()
        return True
    except Exception as e:
        print(f"❌ Chyba: {e}")
        return False


async def test_get_materials():
    """Test načtení materiálů"""
    print("\n📦 Test načtení materiálů...")
    config = Config()
    db = DatabaseManager(config)
    
    try:
        await db.connect()
        
        result = await db.get_materials(limit=5)
        print(f"✅ Načteno {len(result.get('materials', []))} materiálů")
        
        await db.close()
        return True
    except Exception as e:
        print(f"❌ Chyba: {e}")
        return False


async def test_anonymization():
    """Test anonymizace"""
    print("\n🔒 Test anonymizace...")
    config = Config()
    anonymizer = DataAnonymizer(config)
    
    # Test anonymizace zákazníka
    customer_name = "Firma ABC s.r.o."
    anonymized = anonymizer._anonymize_customer_name(customer_name, 123)
    print(f"✅ Zákazník: '{customer_name}' → '{anonymized}'")
    
    # Test anonymizace emailu
    email = "jan.novak@firma.cz"
    anonymized_email = anonymizer._anonymize_email(email)
    print(f"✅ Email: '{email}' → '{anonymized_email}'")
    
    # Test anonymizace telefonu
    phone = "+420 123 456 789"
    anonymized_phone = anonymizer._anonymize_phone(phone)
    print(f"✅ Telefon: '{phone}' → '{anonymized_phone}'")
    
    return True


async def test_response_format():
    """Test formátu odpovědi"""
    print("\n📤 Test formátu odpovědi...")
    response_builder = ResponseBuilder()
    
    # Simulace dat
    mock_data = {
        'orders': [
            {
                'id': '123',
                'code': '2024/001',
                'name': 'Test zakázka',
                'customer_name': 'ZÁKAZNÍK_001',
                'active': 'ANO'
            }
        ],
        'stats': {
            'total': 100,
            'active_count': 80,
            'delayed_count': 5
        }
    }
    
    response = response_builder.build_orders_response(mock_data, {'status': 'ANO'})
    
    # Kontrola struktury
    assert 'status' in response, "Missing 'status' field"
    assert 'action' in response, "Missing 'action' field"
    assert 'data' in response, "Missing 'data' field"
    assert 'message' in response, "Missing 'message' field"
    
    print(f"✅ Struktura odpovědi je správná")
    print(f"   Status: {response['status']}")
    print(f"   Akce: {response['action']['type']}")
    print(f"   Zpráva: {response['message']}")
    
    # Výpis JSON
    print(f"\n   JSON ukázka:")
    print(json.dumps(response, indent=2, ensure_ascii=False)[:500] + "...")
    
    return True


async def run_all_tests():
    """Spuštění všech testů"""
    print("="*60)
    print("eMISTR MCP Server - Testovací sada")
    print("="*60)
    
    tests = [
        ("Připojení k databázi", test_database_connection),
        ("Načtení zakázek", test_get_orders),
        ("Vyhledávání zakázek", test_search_orders),
        ("Načtení zaměstnanců", test_get_workers),
        ("Načtení materiálů", test_get_materials),
        ("Anonymizace dat", test_anonymization),
        ("Formát odpovědi", test_response_format),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Chyba v testu '{test_name}': {e}")
            results.append((test_name, False))
    
    # Souhrn
    print("\n" + "="*60)
    print("SOUHRN TESTŮ")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nVýsledek: {passed}/{total} testů prošlo")
    print("="*60)
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
