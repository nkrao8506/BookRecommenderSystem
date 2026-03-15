'use client';

import { motion } from 'framer-motion';

interface BookCardProps {
  title: string;
  author: string;
  image: string;
  votes?: number;
  rating?: number;
  index: number;
}

export default function BookCard({ title, author, image, votes, rating, index }: BookCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
      whileHover={{ y: -8, transition: { duration: 0.2 } }}
      className="group"
    >
      <div className="relative overflow-hidden rounded-2xl bg-white shadow-md transition-shadow hover:shadow-xl dark:bg-zinc-900">
        <div className="aspect-[2/3] overflow-hidden">
          <img
            src={image}
            alt={title}
            className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-110"
            onError={(e) => {
              (e.target as HTMLImageElement).src = 'https://via.placeholder.com/200x300?text=No+Cover';
            }}
          />
        </div>
        <div className="p-4">
          <h3 className="line-clamp-2 text-lg font-semibold text-zinc-900 dark:text-zinc-100">
            {title}
          </h3>
          <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400">{author}</p>
          {(votes !== undefined || rating !== undefined) && (
            <div className="mt-3 flex items-center gap-2">
              {rating !== undefined && (
                <span className="flex items-center gap-1 text-sm font-medium text-amber-500">
                  <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20">
                    <path d="M10 15l-5.878 3.09 1.123-6.545L.489 6.91l6.572-.955L10 0l2.939 5.955 6.572.955-4.756 4.635 1.123 6.545z" />
                  </svg>
                  {rating}
                </span>
              )}
              {votes !== undefined && (
                <span className="text-xs text-zinc-500 dark:text-zinc-500">
                  ({votes.toLocaleString()} votes)
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
}
