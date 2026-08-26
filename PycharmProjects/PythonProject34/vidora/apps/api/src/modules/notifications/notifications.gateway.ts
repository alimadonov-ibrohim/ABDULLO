import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  ConnectedSocket,
  MessageBody,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { NotificationsService } from './notifications.service';

@WebSocketGateway({
  cors: { origin: '*' },
  namespace: '/ws/notifications',
})
export class NotificationsGateway {
  @WebSocketServer()
  server: Server;

  constructor(private notificationsService: NotificationsService) {}

  handleConnection(client: Socket) {
    const userId = client.handshake.query.userId as string;
    if (userId) {
      client.join(`user:${userId}`);
    }
  }

  @SubscribeMessage('markRead')
  async handleMarkRead(
    @ConnectedSocket() client: Socket,
    @MessageBody() data: { notificationId: string },
  ) {
    const userId = client.handshake.query.userId as string;
    await this.notificationsService.markAsRead(data.notificationId, userId);
    client.emit('notificationRead', { id: data.notificationId });
  }

  @SubscribeMessage('markAllRead')
  async handleMarkAllRead(@ConnectedSocket() client: Socket) {
    const userId = client.handshake.query.userId as string;
    await this.notificationsService.markAllAsRead(userId);
    client.emit('allNotificationsRead');
  }

  sendNotification(userId: string, notification: any) {
    this.server.to(`user:${userId}`).emit('notification', notification);
  }
}
