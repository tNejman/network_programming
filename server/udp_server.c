#define _POSIX_C_SOURCE 200112L
#include <arpa/inet.h>
#include <sys/types.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

#define TRUE 1
#define BSIZE 1024 * 1024

#define bailout(s) {perror(s); exit(1); }
#define notDone() TRUE

#define DEF_PORT "8888"

int moreWork(void) {
    return 1;
}

int send_to_client(int sock,
                   const struct sockaddr *client_addr,
                   socklen_t client_len,
                   const char *response)
{
    ssize_t sent = sendto(sock, response, strlen(response), 0,
                          client_addr, client_len);
    return (int)sent;
}

int main(int argc, char **argv) {
    int sock, rval;
    struct addrinfo *bindto_address;
    struct addrinfo hints;
    char buf[BSIZE];
    char port[6];

    struct sockaddr_storage client_addr;
    socklen_t client_addr_len;

    if (argc > 1 && strlen(argv[1]) <= 5) {
        strcpy(port, argv[1]);
        printf("Defined user port: %s\n", port);
    } else {
        strcpy(port, DEF_PORT);
    }

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_INET; // IPv4 
    hints.ai_socktype = SOCK_DGRAM; // UDP
    hints.ai_flags = AI_PASSIVE;

    if (getaddrinfo(NULL, port, &hints, &bindto_address) != 0)
        bailout("getting local address");

    sock = socket(bindto_address->ai_family,
                  bindto_address->ai_socktype,
                  bindto_address->ai_protocol);
    if (sock == -1)
        bailout("opening datagram socket");

    if (bind(sock, bindto_address->ai_addr, bindto_address->ai_addrlen) == -1)
        bailout("binding datagram socket");

    freeaddrinfo(bindto_address);

    printf("UDP server listening on port %s...\n", port);

    do {
        memset(buf, 0, BSIZE);
        client_addr_len = sizeof(client_addr);

        // receive
        rval = recvfrom(sock, buf, BSIZE - 1, 0,
                        (struct sockaddr *)&client_addr, &client_addr_len);

        if (rval == -1) {
            perror("recvfrom");
            continue;
        }

        /* ensure null-terminated string */
        if (rval >= 0 && rval < BSIZE)
            buf[rval] = '\0';
        else
            buf[BSIZE - 1] = '\0';

        printf("%s: -->%s\n", argv[0], buf);
        printf("datagram size is: %ld", strlen(buf));

        int success = send_to_client(sock,
                                     (struct sockaddr *)&client_addr,
                                     client_addr_len,
                                     "OK");
        printf("Read data successful. Sending: \"OK\"\n");
        if (success == -1) {
            printf("Send to client failed...\n");
        }

        fflush(stdout);

    } while (moreWork());

    close(sock);
    return 0;
}
