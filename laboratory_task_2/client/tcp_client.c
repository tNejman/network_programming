#include <arpa/inet.h>
#include <err.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#define DATA "Half a league, half a league . . ."
#define _USE_RESOLVER
#define _USE_ARGS
#define DEFAULT_PORT 8000
#define DEFAULT_SRV_IP "127.0.0.1"

#define BSIZE 1024

#define bailout(s) { perror( s ); exit(1);  }
#define Usage() { errx( 0, "Usage: %s address-or-ip [port]\n", argv[0]); }


int main(int argc, char *argv[])
{
    int sock = 0;
    struct sockaddr_in server;
    struct hostent *hp = NULL;

    char *server_ip = DEFAULT_SRV_IP;
    int server_port = DEFAULT_PORT;

    if (argc >= 2) {
        server_ip = argv[1];
    }
    if (argc >= 3) {
        server_port = atoi(argv[2]);
    }

    sock = socket( AF_INET, SOCK_STREAM, 0 );
    if (sock == -1) 
        bailout("opening stream socket");

    server.sin_family = AF_INET;

    if (argc < 2) Usage();

    hp = gethostbyname2( server_ip, AF_INET );
    /* hostbyname() returns a struct with resolved host address  */
    if (hp == (struct hostent *) 0) {
        errx(2, "%s: unknown host\n", argv[1]);
    } else {
        memcpy( (char *) &server.sin_addr, (char *) hp->h_addr, hp->h_length);
    }

    server.sin_port = htons(server_port);
// #elif defined(USE_ARGS)
//     if (argc < 3) Usage();
//     inet_aton( argv[1], &server.sin_addr );
//     server.sin_port = htons(atoi(argv[2]));
// #else
//     inet_aton( DEFAULT_SRV_IP, &server.sin_addr );
//     server.sin_port = htons(DEFAULT_PORT);
// #endif

    printf("Connecting...\n");
        if (connect(sock, (struct sockaddr *) &server, sizeof server) == -1) 
            bailout("connecting stream socket");
        printf("Connected.\n");

    while (1) {
        char buf_n1[BSIZE];
        char buf_op[BSIZE];
        char buf_n2[BSIZE];
        char response[BSIZE];

        printf("Input operand no. 1: ");
        scanf("%s", buf_n1);
        buf_n1[BUFSIZ-1] == '\0';
        if (write(sock, buf_n1, strlen(buf_n1)) == -1)
            bailout("writing num1");

        if (buf_n1[0] == 'q') 
            break;

        printf("Input operator: ");
        scanf("%s", buf_op);
        buf_n1[BUFSIZ-1] == '\0';
        if (write(sock, buf_op, strlen(buf_op)) == -1)
            bailout("writing operator");

        printf("Input operand no. 2: ");
        scanf("%s", buf_n2);
        buf_n2[BUFSIZ-1] == '\0';
        if (write(sock, buf_n2, strlen(buf_n2)) == -1)
            bailout("writing num2");

        printf("Performed opeartion: %s %s %s\n", buf_n1, buf_op, buf_n2);

        memset(response, 0, BSIZE);
        if (read(sock, response, BSIZE) == -1)
            bailout("reading from socket");
        printf("Server response: %s\n", response);
    }

    close(sock);
    exit(0);
}
