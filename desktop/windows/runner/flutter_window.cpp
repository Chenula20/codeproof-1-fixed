#include "flutter_window.h"

#include <shobjidl.h>

#include <optional>
#include <string>

#include "flutter/generated_plugin_registrant.h"

namespace {

std::string WideStringToUtf8(const wchar_t* value) {
  if (value == nullptr) {
    return {};
  }

  const int length = WideCharToMultiByte(CP_UTF8, 0, value, -1, nullptr, 0,
                                         nullptr, nullptr);
  if (length <= 1) {
    return {};
  }

  std::string result(static_cast<size_t>(length), '\0');
  WideCharToMultiByte(CP_UTF8, 0, value, -1, result.data(), length, nullptr,
                      nullptr);
  result.resize(static_cast<size_t>(length - 1));
  return result;
}

std::optional<std::string> PickDirectory(HWND owner) {
  IFileDialog* dialog = nullptr;
  HRESULT hr = CoCreateInstance(CLSID_FileOpenDialog, nullptr,
                                CLSCTX_INPROC_SERVER, IID_PPV_ARGS(&dialog));
  if (FAILED(hr)) {
    return std::nullopt;
  }

  FILEOPENDIALOGOPTIONS options;
  hr = dialog->GetOptions(&options);
  if (SUCCEEDED(hr)) {
    dialog->SetOptions(options | FOS_PICKFOLDERS | FOS_FORCEFILESYSTEM);
  }

  hr = dialog->Show(owner);
  if (FAILED(hr)) {
    dialog->Release();
    return std::nullopt;
  }

  IShellItem* item = nullptr;
  hr = dialog->GetResult(&item);
  dialog->Release();
  if (FAILED(hr)) {
    return std::nullopt;
  }

  PWSTR path = nullptr;
  hr = item->GetDisplayName(SIGDN_FILESYSPATH, &path);
  item->Release();
  if (FAILED(hr)) {
    return std::nullopt;
  }

  std::string result = WideStringToUtf8(path);
  CoTaskMemFree(path);
  return result;
}

}  // namespace

FlutterWindow::FlutterWindow(const flutter::DartProject& project)
    : project_(project) {}

FlutterWindow::~FlutterWindow() {}

bool FlutterWindow::OnCreate() {
  if (!Win32Window::OnCreate()) {
    return false;
  }

  RECT frame = GetClientArea();

  // The size here must match the window dimensions to avoid unnecessary surface
  // creation / destruction in the startup path.
  flutter_controller_ = std::make_unique<flutter::FlutterViewController>(
      frame.right - frame.left, frame.bottom - frame.top, project_);
  // Ensure that basic setup of the controller was successful.
  if (!flutter_controller_->engine() || !flutter_controller_->view()) {
    return false;
  }
  RegisterPlugins(flutter_controller_->engine());

  native_channel_ = std::make_unique<
      flutter::MethodChannel<flutter::EncodableValue>>(
      flutter_controller_->engine()->messenger(), "codeproof/native",
      &flutter::StandardMethodCodec::GetInstance());
  native_channel_->SetMethodCallHandler(
      [this](const flutter::MethodCall<flutter::EncodableValue>& call,
             std::unique_ptr<flutter::MethodResult<flutter::EncodableValue>>
                 result) {
        if (call.method_name() != "pick_directory") {
          result->NotImplemented();
          return;
        }

        const std::optional<std::string> selected = PickDirectory(GetHandle());
        if (selected.has_value()) {
          result->Success(flutter::EncodableValue(*selected));
        } else {
          result->Success(flutter::EncodableValue());
        }
      });
  SetChildContent(flutter_controller_->view()->GetNativeWindow());

  flutter_controller_->engine()->SetNextFrameCallback([&]() {
    this->Show();
  });

  // Flutter can complete the first frame before the "show window" callback is
  // registered. The following call ensures a frame is pending to ensure the
  // window is shown. It is a no-op if the first frame hasn't completed yet.
  flutter_controller_->ForceRedraw();

  return true;
}

void FlutterWindow::OnDestroy() {
  native_channel_ = nullptr;
  if (flutter_controller_) {
    flutter_controller_ = nullptr;
  }

  Win32Window::OnDestroy();
}

LRESULT
FlutterWindow::MessageHandler(HWND hwnd, UINT const message,
                              WPARAM const wparam,
                              LPARAM const lparam) noexcept {
  // Give Flutter, including plugins, an opportunity to handle window messages.
  if (flutter_controller_) {
    std::optional<LRESULT> result =
        flutter_controller_->HandleTopLevelWindowProc(hwnd, message, wparam,
                                                      lparam);
    if (result) {
      return *result;
    }
  }

  switch (message) {
    case WM_FONTCHANGE:
      flutter_controller_->engine()->ReloadSystemFonts();
      break;
  }

  return Win32Window::MessageHandler(hwnd, message, wparam, lparam);
}
