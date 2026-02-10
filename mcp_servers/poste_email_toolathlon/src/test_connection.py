#!/usr/bin/env python3
"""
Email Connection Tester
Test IMAP and SMTP server connections
"""

import argparse
import imaplib
import smtplib
import sys
from datetime import datetime

class EmailConnectionTester:
    """Email Connection Tester"""
    
    def __init__(self, email, password, imap_server, imap_port, smtp_server, smtp_port):
        self.email = email
        self.password = password
        self.imap_server = imap_server
        self.imap_port = imap_port
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        
    def _connect_imap(self):
        """Connect to IMAP server"""
        print(f"\n📥 Connecting to IMAP server {self.imap_server}:{self.imap_port}...")
        
        try:
            # Try normal connection first to check server capabilities
            try:
                print("  Trying SSL connection...")
                imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
                print("  ✅ SSL connection successful")
            except:
                print("  SSL connection failed, trying normal connection...")
                imap = imaplib.IMAP4(self.imap_server, self.imap_port)
                # Try STARTTLS
                try:
                    print("  Trying to upgrade to TLS...")
                    imap.starttls()
                    print("  ✅ TLS upgrade successful")
                except Exception as e:
                    print(f"  ⚠️  STARTTLS failed: {e}, continuing with non-encrypted connection")
            
            # Login
            print(f"  Logging in to {self.email}...")
            imap.login(self.email, self.password)
            print("  ✅ IMAP login successful!")
            
            # Get email information
            print("\n📊 Email information:")
            # List all folders
            status, folders = imap.list()
            if status == 'OK':
                print(f"  📁 Folder count: {len(folders)}")
                print("  📁 Folder list:")
                max_display = 5
                for folder in folders[:max_display]:
                    print(f"     - {folder.decode()}")
                if len(folders) > max_display:
                    print(f"     ... {len(folders)-max_display} more folders")
            
            # Select inbox
            status, count = imap.select('INBOX')
            if status == 'OK':
                print(f"  📧 Inbox email count: {count[0].decode()}")
            
            # Close connection
            imap.close()
            imap.logout()
            
            return True
            
        except imaplib.IMAP4.error as e:
            print(f"  ❌ IMAP error: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Connection failed: {type(e).__name__}: {e}")
            return False
    
    def _connect_smtp(self):
        """Connect to SMTP server"""
        print(f"\n📤 Connecting to SMTP server {self.smtp_server}:{self.smtp_port}...")
        
        try:
            # Try SSL connection first, then normal connection if SSL fails
            try:
                print("  Trying SSL connection...")
                smtp = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
                print("  ✅ SSL connection successful")
            except:
                print("  SSL connection failed, trying normal connection...")
                smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
                smtp.set_debuglevel(1)  # Set to 1 to see detailed SMTP conversation
                
                # 打招呼
                smtp.ehlo()
                
                # 检查服务器是否支持STARTTLS
                if smtp.has_extn('STARTTLS'):
                    try:
                        print("  Detected STARTTLS support, trying to upgrade to TLS...")
                        smtp.starttls()
                        print("  Re-doing EHLO handshake...")
                        smtp.ehlo()
                        print("  ✅ TLS upgrade successful")
                    except Exception as e:
                        print(f"  ⚠️  STARTTLS failed: {e}, continuing with non-encrypted connection")
                else:
                    print("  ⚠️  Server does not support STARTTLS")
            
            # Login
            print(f"  Logging in to {self.email}...")
            smtp.login(self.email, self.password)
            print("  ✅ SMTP login successful!")
            
            # Get server information
            print("\n📊 SMTP server features:")
            if hasattr(smtp, 'esmtp_features'):
                max_display = 5
                features = list(smtp.esmtp_features.keys())[:max_display]
                for feature in features:
                    print(f"     - {feature}")
                if len(smtp.esmtp_features) > max_display:
                    print(f"     ... {len(smtp.esmtp_features)-max_display} more features")
            
            # Close connection
            smtp.quit()
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            print("  ❌ SMTP authentication failed: username or password error")
            return False
        except smtplib.SMTPException as e:
            print(f"  ❌ SMTP error: {e}")
            return False
        except Exception as e:
            print(f"  ❌ Connection failed: {type(e).__name__}: {e}")
            return False
    
    def test_all(self):
        """Test all connections"""
        print("=" * 50)
        print(f"📧 Email connection test")
        print(f"⏰ Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        print(f"\n📋 Configuration:")
        print(f"  Email: {self.email}")
        print(f"  IMAP: {self.imap_server}:{self.imap_port}")
        print(f"  SMTP: {self.smtp_server}:{self.smtp_port}")
        
        # Test IMAP
        imap_success = self._connect_imap()
        
        # Test SMTP
        smtp_success = self._connect_smtp()
        
        # Summary
        print("\n" + "=" * 50)
        print("📊 Test results summary:")
        print(f"  IMAP: {'✅ Success' if imap_success else '❌ Failed'}")
        print(f"  SMTP: {'✅ Success' if smtp_success else '❌ Failed'}")
        print("=" * 50)
        
        return imap_success and smtp_success

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Test email server connections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test Gmail
  %(prog)s -e myemail@gmail.com -p mypassword -is imap.gmail.com -ip 993 -ss smtp.gmail.com -sp 587
  
  # Test local Poste.io
  %(prog)s -e user1@mcp.com -p password -is localhost -ip 1143 -ss localhost -sp 2525
  
  # Simplified write (using short parameters)
  %(prog)s -e test@test.com -p pass123 -is localhost -ip 143 -ss localhost -sp 25
        """
    )
    
    # Add parameters
    parser.add_argument('-e', '--email', required=True, help='Email address')
    parser.add_argument('-p', '--password', required=True, help='Email password')
    parser.add_argument('-is', '--imap-server', required=True, help='IMAP server address')
    parser.add_argument('-ip', '--imap-port', type=int, required=True, help='IMAP port (143/993)')
    parser.add_argument('-ss', '--smtp-server', required=True, help='SMTP server address')
    parser.add_argument('-sp', '--smtp-port', type=int, required=True, help='SMTP port (25/465/587)')
    
    # Parse parameters
    args = parser.parse_args()
    
    # Create tester and run
    tester = EmailConnectionTester(
        email=args.email,
        password=args.password,
        imap_server=args.imap_server,
        imap_port=args.imap_port,
        smtp_server=args.smtp_server,
        smtp_port=args.smtp_port
    )
    
    # Run test
    success = tester.test_all()
    
    # Return status code
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()