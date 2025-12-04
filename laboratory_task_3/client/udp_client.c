#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <err.h>
#include <netdb.h>
#include <errno.h>
#include <openssl/sha.h>

#define DEFAULT_SRV_IP "127.0.0.1"
#define DEFAULT_PORT 8888

#define BSIZE 1000
#define DATA_SIZE 10000
#define DATA_PER_PACKET 100
#define PACKET_COUNT DATA_SIZE / DATA_PER_PACKET
#define HEADER_SIZE sizeof(int)

#define TIMEOUT_S 100 // ms

#define bailout(s) { perror( s ); exit(1);  }


int main(int argc, char *argv[]) {
    int sock = 0;
    struct sockaddr_in server;
    struct hostent *hp = NULL;
    char buf[BSIZE];
    char recv_buf[BSIZE];

    socklen_t slen = sizeof(server);

    char *server_ip = DEFAULT_SRV_IP;
    int server_port = DEFAULT_PORT;

    const char RANDOM_LETTER_POOL[] = {'R','E','G','G','I','N'};
    char data[DATA_SIZE];
    char is_packet_sent[PACKET_COUNT];

    struct timeval tv;
    tv.tv_sec = 0;
    tv.tv_usec = TIMEOUT_S * 1000;

    sock = socket(AF_INET, SOCK_DGRAM, 0);
    if (sock == -1)
        bailout("opening stream socket");

    if (setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv)) < 0)
        bailout("Error setting socket timeout");

    if (argc >= 2)
        server_ip = argv[1];
    if (argc >= 3)
        server_port = atoi(argv[2]);

    server.sin_family = AF_INET;
    server.sin_port = htons(server_port);

    if (inet_aton(server_ip, &server.sin_addr) == 0) {
        hp = gethostbyname2( server_ip, AF_INET);
        if (hp == NULL) {
            fprintf(stderr, "%s: unknown host\n", server_ip);
            exit(2);
        } 
        memcpy( (char *) &server.sin_addr, (char *) hp->h_addr, hp->h_length);
    }

    printf("UDP Client started. Sending to %s:%d\n", server_ip, server_port);

    memset(is_packet_sent, '0', PACKET_COUNT);
    for (int i = 0; i < DATA_SIZE; ++i) {
        data[i] = RANDOM_LETTER_POOL[rand() % sizeof(RANDOM_LETTER_POOL)];
    }
    data[DATA_SIZE-1] = '\0';

    int current_pkt = 0;

    while(current_pkt < PACKET_COUNT) {
        memset(buf, 0, BSIZE);
        memset(recv_buf, 0, BSIZE);

        int offset = current_pkt * DATA_PER_PACKET;
        uint32_t pkt_net = htonl((uint32_t)current_pkt);

        memcpy(buf, &pkt_net, sizeof(int));
        memcpy(buf + HEADER_SIZE, data + offset, DATA_PER_PACKET);
        
        int total_len = HEADER_SIZE + DATA_PER_PACKET;

        printf("Sending Packet %d/%d (%d bytes)...\n", current_pkt, PACKET_COUNT, total_len);
        //printf("Packet content: %.*s", DATA_PER_PACKET+1, buf);
        printf("Packet content: %.*s\n", DATA_PER_PACKET + 1 - 4, buf + 4);

        if (sendto(sock, buf, total_len, 0, (struct sockaddr*) &server, slen) == -1) {
            bailout("sendto()");
        }

        int recv_len = recvfrom(sock, recv_buf, BSIZE, 0, (struct sockaddr*) &server, &slen);

        if (recv_len > 0) {
            recv_buf[recv_len] = '\0';
            

            uint32_t ack_net;
            memcpy(&ack_net, recv_buf, sizeof(ack_net));
            int ack = (int)ntohl(ack_net);
            printf("Received ACK: %d \n", ack);

            if (memcmp(&ack, &current_pkt, sizeof(int)) == 0) {
                is_packet_sent[current_pkt] = 1;
                ++current_pkt; 
            }
        } 
        else {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                printf("Timeout occurred! Resending packet %d...\n", current_pkt);
            } else {
                bailout("recvfrom error");
            }
        }
    }

    unsigned char hash_digest[SHA256_DIGEST_LENGTH];
    if (SHA256((const unsigned char *)data, DATA_SIZE, hash_digest) == NULL) {
        fprintf(stderr, "SHA256 calculation failed.\n");
        return 1;
    }

    for (int i = 0; i < SHA256_DIGEST_LENGTH; ++i) {
        printf("%02x", hash_digest[i]);
    }
    printf("\n");
    printf("Done\n");

    close(sock);
    return 0;
}
