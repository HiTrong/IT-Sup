import { StyleSheet, Text, View, StatusBar, Image, TouchableOpacity, Alert } from 'react-native'
import React, { useEffect, useRef, useState } from 'react'
import LottieView from "lottie-react-native";
import { Audio } from "expo-av";
import * as FileSystem from 'expo-file-system';
import axios from 'axios';
import { LinearGradient } from 'expo-linear-gradient'
import { scale, verticalScale } from "react-native-size-matters";
import FontAwesome from "@expo/vector-icons/FontAwesome";
import { Buffer } from 'buffer';


export default function HomeScreen() {
  const [text, setText] = useState("");
  const [isRecording, setIsRecording] = useState(false);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [loading, setLoading] = useState(false);
  const [recordingPath, setRecordingPath] = useState<string | null>(null);
  const sound = useRef(new Audio.Sound());

  useEffect(() => {
    return () => {
      sound.current.unloadAsync().catch((error) => {
        console.error("Error unloading sound:", error);
      });
    };
  }, []);
  
  const lottieRef = useRef<LottieView>(null);

  // Hàm bắt đầu ghi âm
  const startRecording = async () => {    
    try {
      const permission = await Audio.requestPermissionsAsync();
      if (!permission.granted) {
        alert("Microphone đã bị từ chối quyền truy cập!");
        return;
      }

      const { recording } = await Audio.Recording.createAsync(
        Audio.RecordingOptionsPresets.HIGH_QUALITY
      );
      setRecording(recording);
      setIsRecording(true);
      console.log("Recording started");
    } catch (error) {
      console.error("Failed to start recording", error);
    }
};

  // Hàm dừng ghi âm và gửi file đến API
  const stopRecording = async () => {
    try {
      setIsRecording(false);
      await recording.stopAndUnloadAsync();
      await Audio.setAudioModeAsync(
        {
          allowsRecordingIOS: false,
        }
      );
      const uri = recording.getURI();
      console.log("Recording stopped and saved at: ", uri);
      if (uri) {
        sendAudioToAPI(uri)
        // playAudio(uri);
      }
    } catch (error) {
      console.error("Failed to stop recording", error);
    }

  };


  // Gửi file ghi âm đến API của bạn
  const sendAudioToAPI = async (uri) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append("audio", {
        uri,
        type: "audio/m4a", // Hoặc kiểu file tương ứng
        name: "recorded_audio.m4a",
      } as any);

      const response = await axios.post("http://10.0.2.2:5000/process-audio", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        responseType: "arraybuffer", // Nhận file audio từ API
        withCredentials: true,
        timeout: 300000
      });    

      // Convert arraybuffer → base64
      const base64Audio = Buffer.from(response.data, "binary").toString("base64");

      const aiAudioPath = `${FileSystem.documentDirectory}/ai_response.mp3`;
      await FileSystem.writeAsStringAsync(aiAudioPath, base64Audio, {
        encoding: FileSystem.EncodingType.Base64,
      });
      playAudio(aiAudioPath);
    } catch (error) {
      console.error("API Error:", error);
      Alert.alert("Lỗi", "Không thể gửi file ghi âm.");
    }
    setLoading(false);
  };

  // Phát âm thanh phản hồi từ AI
  const playAudio = async (uri) => {
    await Audio.setAudioModeAsync({
      allowsRecordingIOS: false, // Không cần ghi âm khi phát
      playsInSilentModeIOS: true, // Phát âm thanh ngay cả khi thiết bị ở chế độ im lặng
      staysActiveInBackground: true, // Giữ âm thanh hoạt động trong nền
    });

    try {
      console.log("Playing audio from: ", uri);

      // Kiểm tra tệp có tồn tại không
    const fileInfo = await FileSystem.getInfoAsync(uri);
    if (!fileInfo.exists) {
      console.error("File does not exist at the given URI.");
      return;
    }

      // Unload the previous sound if it exists
      if (sound.current) {
        await sound.current.unloadAsync();
      }

      // Create and play the new sound
      const { sound: newSound } = await Audio.Sound.createAsync({ uri });
      sound.current = newSound;
      await sound.current.playAsync();
    } catch (error) {
      console.error("Error playing sound:", error);
    }
  };
  
  return (
    <LinearGradient colors={["#1e126e", "#06014b"]} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} style={styles.container}>
      <StatusBar barStyle={"light-content"} />
      <Image source={require("@/assets/main/blur.png")} style={{ position: "absolute", right: scale(-15), top: 0, width: scale(240) }} />
      <Image source={require("@/assets/main/purple-blur.png")} style={{ position: "absolute", left: scale(-15), bottom: verticalScale(100), width: scale(210) }} />
      <View style={{ marginTop: verticalScale(-40) }}>
        {loading ? (
          <TouchableOpacity>
            <LottieView source={require("@/assets/animations/loading.json")} autoPlay loop speed={1.3} style={{ width: scale(270), height: scale(270) }} />
          </TouchableOpacity>
        ) : (
          <>
            {!isRecording ? (
              <TouchableOpacity
                style={{ width: scale(110), height: scale(110), backgroundColor: "#fff", flexDirection: "row", alignItems: "center", justifyContent: "center", borderRadius: scale(100) }}
                onPress={startRecording}
              >
                <FontAwesome name="microphone" size={scale(50)} color="#2b3356" />
                </TouchableOpacity>
            ) : (
              <TouchableOpacity onPress={stopRecording}>
                <LottieView source={require("@/assets/animations/animation.json")} autoPlay loop speed={1.3} style={{ width: scale(250), height: scale(250) }} />
              </TouchableOpacity>
            )}
            </>
          )}
      </View>
      <View style={{ alignItems: "center", width: scale(350), position: "absolute", bottom: verticalScale(90) }}>
        <Text style={{ color: "#fff", fontSize: scale(16), width: scale(269), textAlign: "center", lineHeight: 25 }}>
          {loading ? "Đang xử lý..." : isRecording ? "Đang ghi âm..." : "Nhấn micro để bắt đầu thu âm!"}
        </Text>
      </View>
    </LinearGradient>
  );

}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    backgroundColor: "#131313",
  },
});