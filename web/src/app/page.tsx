import Navbar from '@/components/Navbar';
import BookCard from '@/components/BookCard';

async function getPopularBooks() {
  try {
    const res = await fetch('http://127.0.0.1:8000/api/', {
      cache: 'no-store',
    });
    if (!res.ok) {
      throw new Error('Failed to fetch books');
    }
    return res.json();
  } catch (error) {
    console.error('Error fetching books:', error);
    return { books: [] };
  }
}

export default async function Home() {
  const data = await getPopularBooks();

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-black">
      <Navbar />
      
      <main className="pt-24">
        <section className="relative overflow-hidden px-6 py-16 sm:py-24">
          <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-violet-100 via-transparent to-transparent dark:from-violet-950/30" />
          
          <div className="mx-auto max-w-7xl">
            <div className="mb-12 text-center sm:text-left">
              <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-5xl lg:text-6xl">
                Discover Your Next
                <span className="block bg-gradient-to-r from-violet-600 to-indigo-600 bg-clip-text text-transparent">
                  Favorite Book
                </span>
              </h1>
              <p className="mt-4 max-w-2xl text-lg text-zinc-600 dark:text-zinc-400">
                Explore our curated collection of trending books loved by readers worldwide.
              </p>
            </div>

            <div className="mb-8 flex items-center gap-3">
              <span className="flex h-3 w-3">
                <span className="flex h-3 w-3 rounded-full bg-violet-500" />
              </span>
              <h2 className="text-xl font-semibold text-zinc-900 dark:text-zinc-100">
                Trending Now
              </h2>
            </div>

            {data.books && data.books.length > 0 ? (
              <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 sm:gap-6 md:grid-cols-4 lg:grid-cols-5">
                {data.books.map((book: { title: string; author: string; image: string; votes: number; rating: number }, index: number) => (
                  <BookCard
                    key={`${book.title}-${index}`}
                    title={book.title}
                    author={book.author}
                    image={book.image}
                    votes={book.votes}
                    rating={book.rating}
                    index={index}
                  />
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <div className="mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800">
                  <svg className="h-8 w-8 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <p className="text-zinc-500 dark:text-zinc-400">
                  Unable to load books. Make sure Django server is running on port 8000.
                </p>
              </div>
            )}
          </div>
        </section>
      </main>
    </div>
  );
}
