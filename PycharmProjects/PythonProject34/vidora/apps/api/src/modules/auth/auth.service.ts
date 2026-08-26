import { Injectable, UnauthorizedException, ConflictException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { PrismaService } from '../../prisma/prisma.service';
import * as bcrypt from 'bcryptjs';
import { v4 as uuidv4 } from 'uuid';

@Injectable()
export class AuthService {
  constructor(
    private prisma: PrismaService,
    private jwtService: JwtService,
    private configService: ConfigService,
  ) {}

  async register(dto: { email: string; username: string; password: string; dateOfBirth?: string }) {
    const existingUser = await this.prisma.user.findFirst({
      where: {
        OR: [
          { email: dto.email },
          { username: dto.username },
        ],
      },
    });

    if (existingUser) {
      if (existingUser.email === dto.email) {
        throw new ConflictException('Email already registered');
      }
      throw new ConflictException('Username already taken');
    }

    const passwordHash = await bcrypt.hash(dto.password, 12);

    const user = await this.prisma.user.create({
      data: {
        email: dto.email,
        username: dto.username,
        passwordHash,
        dateOfBirth: dto.dateOfBirth ? new Date(dto.dateOfBirth) : undefined,
        channel: {
          create: {
            name: dto.username,
            handle: dto.username.toLowerCase().replace(/[^a-z0-9_]/g, ''),
            description: '',
          },
        },
      },
      include: {
        channel: true,
      },
    });

    const tokens = await this.generateTokens(user.id, user.email, user.role);
    await this.saveRefreshToken(user.id, tokens.refreshToken);

    return {
      ...tokens,
      user: this.sanitizeUser(user),
    };
  }

  async login(email: string, password: string) {
    const user = await this.prisma.user.findUnique({
      where: { email },
      include: { channel: true },
    });

    if (!user || !user.passwordHash) {
      throw new UnauthorizedException('Invalid credentials');
    }

    const isPasswordValid = await bcrypt.compare(password, user.passwordHash);
    if (!isPasswordValid) {
      throw new UnauthorizedException('Invalid credentials');
    }

    const tokens = await this.generateTokens(user.id, user.email, user.role);
    await this.saveRefreshToken(user.id, tokens.refreshToken);

    return {
      ...tokens,
      user: this.sanitizeUser(user),
    };
  }

  async refreshTokens(refreshToken: string) {
    const tokenRecord = await this.prisma.refreshToken.findUnique({
      where: { token: refreshToken },
      include: { user: { include: { channel: true } } },
    });

    if (!tokenRecord || tokenRecord.expiresAt < new Date()) {
      throw new UnauthorizedException('Invalid or expired refresh token');
    }

    await this.prisma.refreshToken.delete({ where: { id: tokenRecord.id } });

    const tokens = await this.generateTokens(
      tokenRecord.userId,
      tokenRecord.user.email,
      tokenRecord.user.role,
    );
    await this.saveRefreshToken(tokenRecord.userId, tokens.refreshToken);

    return {
      ...tokens,
      user: this.sanitizeUser(tokenRecord.user),
    };
  }

  async logout(refreshToken: string) {
    await this.prisma.refreshToken.deleteMany({
      where: { token: refreshToken },
    });
  }

  async getProfile(userId: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      include: {
        channel: true,
        _count: {
          select: {
            subscriptions: true,
          },
        },
      },
    });

    if (!user) throw new UnauthorizedException('User not found');
    return this.sanitizeUser(user);
  }

  async validateGoogleUser(profile: any) {
    let user = await this.prisma.user.findUnique({
      where: { googleId: profile.id },
    });

    if (!user) {
      user = await this.prisma.user.findUnique({
        where: { email: profile.emails[0].value },
      });
    }

    if (user) {
      user = await this.prisma.user.update({
        where: { id: user.id },
        data: {
          googleId: profile.id,
          avatar: user.avatar || profile.photos?.[0]?.value,
          isEmailVerified: true,
        },
      });
    } else {
      const username = profile.emails[0].value.split('@')[0] + '_' + uuidv4().slice(0, 6);
      user = await this.prisma.user.create({
        data: {
          email: profile.emails[0].value,
          username,
          avatar: profile.photos?.[0]?.value,
          googleId: profile.id,
          isEmailVerified: true,
          channel: {
            create: {
              name: profile.displayName || username,
              handle: username.toLowerCase().replace(/[^a-z0-9_]/g, ''),
              avatar: profile.photos?.[0]?.value,
            },
          },
        },
      });
    }

    const tokens = await this.generateTokens(user.id, user.email, user.role);
    await this.saveRefreshToken(user.id, tokens.refreshToken);

    return {
      ...tokens,
      user: this.sanitizeUser(user),
    };
  }

  async validateGithubUser(profile: any) {
    let user = await this.prisma.user.findUnique({
      where: { githubId: profile.id },
    });

    if (!user) {
      const email = profile.emails?.[0]?.value || `${profile.username}@github.local`;
      user = await this.prisma.user.findUnique({ where: { email } });
    }

    if (user) {
      user = await this.prisma.user.update({
        where: { id: user.id },
        data: {
          githubId: profile.id,
          avatar: user.avatar || profile.photos?.[0]?.value,
        },
      });
    } else {
      const username = profile.username || `user_${uuidv4().slice(0, 6)}`;
      const email = profile.emails?.[0]?.value || `${username}@github.local`;
      user = await this.prisma.user.create({
        data: {
          email,
          username,
          avatar: profile.photos?.[0]?.value,
          githubId: profile.id,
          channel: {
            create: {
              name: profile.displayName || username,
              handle: username.toLowerCase().replace(/[^a-z0-9_]/g, ''),
              avatar: profile.photos?.[0]?.value,
            },
          },
        },
      });
    }

    const tokens = await this.generateTokens(user.id, user.email, user.role);
    await this.saveRefreshToken(user.id, tokens.refreshToken);

    return {
      ...tokens,
      user: this.sanitizeUser(user),
    };
  }

  private async generateTokens(userId: string, email: string, role: string) {
    const payload = { sub: userId, email, role };

    const [accessToken, refreshToken] = await Promise.all([
      this.jwtService.signAsync(payload, {
        secret: this.configService.get('JWT_SECRET'),
        expiresIn: this.configService.get('JWT_EXPIRATION', '15m'),
      }),
      this.jwtService.signAsync(payload, {
        secret: this.configService.get('REFRESH_TOKEN_SECRET'),
        expiresIn: this.configService.get('REFRESH_TOKEN_EXPIRATION', '7d'),
      }),
    ]);

    return { accessToken, refreshToken };
  }

  private async saveRefreshToken(userId: string, token: string) {
    const expiresAt = new Date();
    expiresAt.setDate(expiresAt.getDate() + 7);

    await this.prisma.refreshToken.create({
      data: {
        userId,
        token,
        expiresAt,
      },
    });
  }

  private sanitizeUser(user: any) {
    const { passwordHash, googleId, githubId, ...sanitized } = user;
    return sanitized;
  }
}
