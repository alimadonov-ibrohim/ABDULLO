import { PrismaClient } from '@prisma/client';
import * as bcrypt from 'bcryptjs';

const prisma = new PrismaClient();

async function main() {
  console.log('Seeding database...');

  // Create categories
  const categories = await Promise.all([
    prisma.category.upsert({ where: { slug: 'music' }, update: {}, create: { name: 'Music', slug: 'music', icon: 'music' } }),
    prisma.category.upsert({ where: { slug: 'gaming' }, update: {}, create: { name: 'Gaming', slug: 'gaming', icon: 'gamepad' } }),
    prisma.category.upsert({ where: { slug: 'programming' }, update: {}, create: { name: 'Programming', slug: 'programming', icon: 'code' } }),
    prisma.category.upsert({ where: { slug: 'news' }, update: {}, create: { name: 'News', slug: 'news', icon: 'newspaper' } }),
    prisma.category.upsert({ where: { slug: 'education' }, update: {}, create: { name: 'Education', slug: 'education', icon: 'graduation-cap' } }),
    prisma.category.upsert({ where: { slug: 'sports' }, update: {}, create: { name: 'Sports', slug: 'sports', icon: 'trophy' } }),
    prisma.category.upsert({ where: { slug: 'movies' }, update: {}, create: { name: 'Movies', slug: 'movies', icon: 'film' } }),
    prisma.category.upsert({ where: { slug: 'technology' }, update: {}, create: { name: 'Technology', slug: 'technology', icon: 'cpu' } }),
    prisma.category.upsert({ where: { slug: 'comedy' }, update: {}, create: { name: 'Comedy', slug: 'comedy', icon: 'smile' } }),
    prisma.category.upsert({ where: { slug: 'travel' }, update: {}, create: { name: 'Travel', slug: 'travel', icon: 'map' } }),
  ]);

  console.log(`Created ${categories.length} categories`);

  // Create demo user
  const passwordHash = await bcrypt.hash('password123', 12);

  const adminUser = await prisma.user.upsert({
    where: { email: 'admin@vidora.com' },
    update: {},
    create: {
      email: 'admin@vidora.com',
      username: 'admin',
      passwordHash,
      role: 'SUPER_ADMIN',
      isEmailVerified: true,
      channel: {
        create: {
          name: 'VIDORA Official',
          handle: 'vidora-official',
          description: 'Official VIDORA channel',
          isVerified: true,
        },
      },
    },
    include: { channel: true },
  });

  const demoUser = await prisma.user.upsert({
    where: { email: 'demo@vidora.com' },
    update: {},
    create: {
      email: 'demo@vidora.com',
      username: 'demo_creator',
      passwordHash,
      role: 'CREATOR',
      isEmailVerified: true,
      channel: {
        create: {
          name: 'Demo Creator',
          handle: 'demo-creator',
          description: 'Demo channel for testing',
        },
      },
    },
    include: { channel: true },
  });

  console.log('Created demo users');

  // Create demo tags
  const tags = await Promise.all([
    prisma.tag.upsert({ where: { slug: 'javascript' }, update: {}, create: { name: 'JavaScript', slug: 'javascript' } }),
    prisma.tag.upsert({ where: { slug: 'tutorial' }, update: {}, create: { name: 'Tutorial', slug: 'tutorial' } }),
    prisma.tag.upsert({ where: { slug: 'webdev' }, update: {}, create: { name: 'Web Dev', slug: 'webdev' } }),
    prisma.tag.upsert({ where: { slug: 'react' }, update: {}, create: { name: 'React', slug: 'react' } }),
    prisma.tag.upsert({ where: { slug: 'nextjs' }, update: {}, create: { name: 'Next.js', slug: 'nextjs' } }),
  ]);

  console.log('Created tags');
  console.log('Seeding completed!');
  console.log('');
  console.log('Demo accounts:');
  console.log('  Admin: admin@vidora.com / password123');
  console.log('  Demo:  demo@vidora.com / password123');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
