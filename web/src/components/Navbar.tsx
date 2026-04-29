'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import LoginModal from './LoginModal';

const navItems = [
  { name: 'Home', href: '/' },
  { name: 'Discover', href: '/recommend' },
  { name: 'Add Book', href: '/upload' },
];

export default function Navbar() {
  const pathname = usePathname();
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetch('http://localhost:8000/api/auth/profile/', {
        headers: {
          'Authorization': `Token ${token}`
        }
      })
      .then(res => res.json())
      .then(data => {
        if (data.user) {
          setUser(data.user);
        }
      })
      .catch(console.error);
    }
  }, []);

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
  };

  return (
    <>
      <motion.nav
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
        className="fixed top-0 left-0 right-0 z-40 border-b border-white/20 bg-white/10 backdrop-blur-xl dark:border-zinc-800/50 dark:bg-zinc-950/50"
      >
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link href="/" className="flex items-center gap-2">
            <motion.div
              whileHover={{ rotate: 15, scale: 1.1 }}
              transition={{ type: 'spring', stiffness: 400 }}
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600/80 to-indigo-600/80 text-white shadow-lg backdrop-blur-sm border border-white/20"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </motion.div>
            <span className="text-xl font-bold text-zinc-900 dark:text-zinc-100">
              BookWise
            </span>
          </Link>

          <div className="flex items-center gap-1">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`relative px-4 py-2 text-sm font-medium transition-colors ${
                  pathname === item.href
                    ? 'text-violet-600 dark:text-violet-400'
                    : 'text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100'
                }`}
              >
                {pathname === item.href && (
                  <motion.div
                    layoutId="navbar-indicator"
                    className="absolute inset-x-2 -bottom-px h-px bg-violet-600 dark:bg-violet-400"
                    transition={{ type: 'spring', bounce: 0.2, duration: 0.6 }}
                  />
                )}
                {item.name}
              </Link>
            ))}
            {user ? (
              <div className="flex items-center gap-4 ml-4 pl-4 border-l border-zinc-200 dark:border-zinc-800">
                <Link href="/history" className="text-sm font-medium text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100">History</Link>
                <span className="text-sm font-medium text-violet-600 dark:text-violet-400">{user.username}</span>
                <button onClick={handleLogout} className="text-sm font-medium text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-zinc-100">Logout</button>
              </div>
            ) : (
              <button 
                onClick={() => setIsLoginOpen(true)}
                className="ml-4 rounded-lg bg-white/10 px-4 py-2 text-sm font-medium text-zinc-900 dark:text-zinc-100 border border-white/20 backdrop-blur-md hover:bg-white/20 transition-all shadow-sm"
              >
                Login
              </button>
            )}
          </div>
        </div>
      </motion.nav>

      <LoginModal 
        isOpen={isLoginOpen} 
        onClose={() => setIsLoginOpen(false)} 
        onLogin={(u) => setUser(u)} 
      />
    </>
  );
}
