#ifndef HANDLE_H
#define HANDLE_H
#include <system_error>
#include <string>
#include <utility>

#include <fcntl.h>
#include <stdio.h>
#include <stdarg.h>
#include <unistd.h>
#include <sys/ioctl.h>

class handle {
public:
    handle() : fd_(-1) {}
    explicit handle(int fd) : fd_(fd) {}
    handle(const char* pathname, int flags, mode_t mode = 0666) {
        fd_ = ::open(pathname, flags, mode);
        if (fd_ == -1) {
            throw std::system_error(errno, std::generic_category());
        }
    }
    ~handle() { if (fd_ != -1) ::close(fd_); }

    handle(const handle&) = delete;
    handle(handle&& h) : fd_(h.fd_) { h.fd_ = -1; }
    handle& operator=(const handle&) = delete;
    handle& operator=(handle&& h) { h.swap(*this); return *this; }

    operator int()  const { return fd_; }
    operator bool() const { return fd_ != -1; }

    void close() {
        int fd = fd_;
        fd_ = -1;
        if ((fd != -1) && ::close(fd)) {
            throw std::system_error(errno, std::generic_category());
        }
    }

    void open(const char* pathname, int flags, mode_t mode = 0666) {
        handle(pathname, flags, mode).swap(*this);
    }

    void swap(handle& h) { std::swap(fd_, h.fd_); }

    size_t read(void* buf, size_t count) const {
        ssize_t bytes = ::read(fd_, buf, count);
        if (bytes < 0) {
            throw std::system_error(errno, std::generic_category());
        }
        return bytes;
    }

    size_t write(const void* buf, size_t count) const {
        ssize_t bytes = ::write(fd_, buf, count);
        if (bytes < 0) {
            throw std::system_error(errno, std::generic_category());
        }
        return bytes;
    }

    int ioctl(int request, void* argp) const {
        int result = ::ioctl(fd_, request, argp);
        if (result < 0) {
            throw std::system_error(errno, std::generic_category());
        }
        return result;
    }
private:
    int fd_;
};

class stdio_handle {
public:
    stdio_handle() : fp_(nullptr) {}
    explicit stdio_handle(FILE* fp) : fp_(fp) {}
    stdio_handle(const char* pathname, const char* mode) {
        fp_ = ::fopen(pathname, mode);
        if (!fp_) {
            throw std::system_error(errno, std::generic_category());
        }
    }
    ~stdio_handle() { if (fp_) ::fclose(fp_); }

    stdio_handle(const stdio_handle&) = delete;
    stdio_handle(stdio_handle&& h) : fp_(h.fp_) { h.fp_ = nullptr; }
    stdio_handle& operator=(const stdio_handle&) = delete;
    stdio_handle& operator=(stdio_handle&& h) { h.swap(*this); return *this; }

    operator FILE*() const { return fp_; }
    operator bool()  const { return fp_; }

    void close() {
        FILE* fp = fp_;
        fp_ = nullptr;
        if (fp && ::fclose(fp)) {
            throw std::system_error(errno, std::generic_category());
        }
    }

    void open(const char* pathname, const char* mode) {
        stdio_handle(pathname, mode).swap(*this);
    }

    void swap(stdio_handle& h) { std::swap(fp_, h.fp_); }

    template<typename T>
    bool read(T& buf) const {
        return static_cast<bool>(read(&buf, sizeof(T), 1));
    }

    template<typename T, size_t N>
    size_t read(T (&buf)[N]) const {
        return read(&buf, sizeof(T), N);
    }

    size_t read(void* buf, size_t size, size_t nmemb = 1) const {
        size_t count = ::fread(buf, size, nmemb, fp_);
        if (!count && ferror(fp_)) {
            clearerr(fp_);
            throw std::system_error(errno, std::generic_category());
        }
        return count;
    }

    template<typename T>
    bool write(const T& buf) const {
        return static_cast<bool>(write(&buf, sizeof(T), 1));
    }

    template<typename T, size_t N>
    size_t write(const T (&buf)[N]) const {
        return write(&buf, sizeof(T), N);
    }

    size_t write(const void* buf, size_t size, size_t nmemb = 1) const {
        size_t count = ::fwrite(buf, size, nmemb, fp_);
        if (!count && ferror(fp_)) {
            clearerr(fp_);
            throw std::system_error(errno, std::generic_category());
        }
        return count;
    }

    std::string readline() const {
        std::string result;
        char buffer[128];
        for (;;) {
            if (fgets(buffer, sizeof(buffer), fp_)) {
                result.append(buffer);
                if (result.back() == '\n') {
                    return result;
                }
            } else if (ferror(fp_)) {
                clearerr(fp_);
                throw std::system_error(errno, std::generic_category());
            } else {
                return result;
            }
        }
    }

    int printf(const char* format, ...) const {
        va_list ap;
        va_start(ap, format);
        int result = vprintf(format, ap);
        va_end(ap);
        return result;
    }

    int vprintf(const char* format, va_list ap) const {
        int result = ::vfprintf(fp_, format, ap);
        if ((result < 0) && ferror(fp_)) {
            clearerr(fp_);
            throw std::system_error(errno, std::generic_category());
        }
        return result;
    }

    int scanf(const char* format, ...) const {
        va_list ap;
        va_start(ap, format);
        int result = vscanf(format, ap);
        va_end(ap);
        return result;
    }

    int vscanf(const char* format, va_list ap) const {
        int result = ::vfscanf(fp_, format, ap);
        if ((result < 0) && ferror(fp_)) {
            clearerr(fp_);
            throw std::system_error(errno, std::generic_category());
        }
        return result;
    }
private:
    FILE* fp_;
};

#endif //HANDLE_H
