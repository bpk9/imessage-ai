import type { Metadata } from "next";
import "./globals.css";
import Link from "next/link";

export const metadata: Metadata = {
  title: "iMessage AI",
  description: "Chat with your iMessage history using AI",
};

function Navigation() {
  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link href="/" className="text-xl font-bold text-gray-900">
              iMessage AI
            </Link>
            <div className="flex space-x-6">
              <Link 
                href="/" 
                className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
              >
                Chat
              </Link>
              <Link 
                href="/conversations" 
                className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
              >
                Conversations
              </Link>
              <Link 
                href="/search" 
                className="text-gray-600 hover:text-gray-900 px-3 py-2 text-sm font-medium"
              >
                Search
              </Link>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="text-xs text-gray-500">Fully Local • Privacy First</span>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        <div className="min-h-screen bg-gray-50">
          <Navigation />
          <main>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}