import {
  Dimensions,
  NativeScrollEvent,
  NativeSyntheticEvent,
  Pressable,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  View,
  Alert
} from "react-native";
import React, { useRef, useState } from "react";
import { LinearGradient } from "expo-linear-gradient";
import { onBoardingData } from "@/configs/constans";
import { scale, verticalScale } from "react-native-size-matters";
import { useFonts } from "expo-font";
import AntDesign from "@expo/vector-icons/AntDesign";
import AsyncStorage from '@react-native-async-storage/async-storage';
import { router } from "expo-router";
import { Audio } from "expo-av";
import axios from 'axios';
import * as FileSystem from 'expo-file-system';
import { Buffer } from 'buffer';

export default function OnBoardingScreen() {
  let [fontsLoaded, fontError] = useFonts({
    SegoeUI: require("../assets/fonts/Segoe-UI.ttf"),
  });

  if (!fontsLoaded && !fontError) {
    return null;
  }

  const [activeIndex, setActiveIndex] = useState(0);
  const scrollViewRef = useRef<ScrollView>(null);
  const [loading, setLoading] = useState(false);
  const [first_speak, setfirst_speak] = useState(false);
  const sound = useRef(new Audio.Sound());

  const GetAudio = async (text) => {
    setLoading(true);
    try {
      // Gửi văn bản để API tạo giọng đọc
      const response = await axios.post("http://10.0.2.2:5000/get-audio", {
        text: text,  // Gửi văn bản dưới dạng JSON
      }, {
        headers: { "Content-Type": "application/json" }, // Đảm bảo content-type là JSON
        responseType: "arraybuffer", // Nhận dữ liệu âm thanh dưới dạng arraybuffer từ API
        withCredentials: true
      });

      const base64Audio = Buffer.from(response.data, "binary").toString("base64");

      const aiAudioPath = `${FileSystem.documentDirectory}/ai_response.mp3`;
      await FileSystem.writeAsStringAsync(aiAudioPath, base64Audio, {
        encoding: FileSystem.EncodingType.Base64,
      });
      playAudio(aiAudioPath);
    } catch (error) {
      console.error("API Error:", error);
      Alert.alert("Lỗi", "Lỗi hệ thống");
      }
      setLoading(false);
    };
  

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

  const handleScroll = (event: NativeSyntheticEvent<NativeScrollEvent>) => {
    const contentOffsetX = event.nativeEvent.contentOffset.x;
    const currentIndex = Math.round(
      contentOffsetX / event.nativeEvent.layoutMeasurement.width
    );
    setActiveIndex(currentIndex);

    // if (onBoardingData[currentIndex]?.title && loading==false) {
    //   GetAudio(onBoardingData[currentIndex]?.title);
    // }

  };

  if (first_speak == false && loading==false) {
    GetAudio("Chào mừng bạn đến với chát bót ai ti súp hỗ trợ sinh viên. Hãy bỏ qua phần quảng cáo để trò chuyện cùng mình nhé!");
    setfirst_speak(true)
  }


  const handleSkip = async () => {
    const nextIndex = activeIndex + 1;

    if(nextIndex < onBoardingData.length){
      scrollViewRef.current?.scrollTo({
        x: Dimensions.get("window").width * nextIndex,
        animated: true,
      });
      setActiveIndex(nextIndex);
    } else {
       await AsyncStorage.setItem('onboarding', 'true');
       router.push("/(routes)/home");
    }
  }

  return (
    <LinearGradient
      colors={["#1e126e", "#06014b"]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.container}
    >
      <StatusBar barStyle="light-content" />
      <Pressable
        style={styles.skipContainer}
        onPress={handleSkip}
      >
        <Text style={styles.skipText}>Skip</Text>
        <AntDesign name="arrowright" size={scale(18)} color="white" />
      </Pressable>
      <ScrollView
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onScroll={handleScroll}
        ref={scrollViewRef}
      >
        {onBoardingData.map((item: onBoardingDataType, index: number) => (
          <View key={index} style={styles.slide}>
            {item.image}
            <Text style={styles.title}>{item.title}</Text>
            <Text style={styles.subtitle}>{item.subtitle}</Text>
          </View>
        ))}
      </ScrollView>
      <View style={styles.paginationContainer}>
        {onBoardingData.map((_, index) => (
          <View
            key={index}
            style={[
              styles.dot,
              {
                opacity: activeIndex === index ? 1 : 0.3,
              },
            ]}
          />
        ))}
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  slide: {
    width: Dimensions.get("window").width,
    justifyContent: "center",
    alignItems: "center",
  },
  title: {
    color: "#fff",
    fontSize: scale(23),
    fontFamily: "SegoeUI",
    textAlign: "center",
    fontWeight: "500",
  },
  subtitle: {
    width: scale(290),
    marginHorizontal: "auto",
    color: "#9A9999",
    fontSize: scale(14),
    fontFamily: "SegoeUI",
    textAlign: "center",
    fontWeight: "400",
    paddingTop: verticalScale(10),
  },
  paginationContainer: {
    position: "absolute",
    bottom: verticalScale(70),
    flexDirection: "row",
    justifyContent: "center",
    alignItems: "center",
    gap: scale(8),
  },
  dot: {
    width: scale(8),
    height: scale(8),
    borderRadius: 100,
    backgroundColor: "#fff",
    marginHorizontal: scale(2),
  },
  skipContainer: {
    position: "absolute",
    top: verticalScale(45),
    right: scale(30),
    flexDirection: "row",
    alignItems: "center",
    gap: scale(5),
    zIndex: 100,
  },
  skipText: {
    color: "#fff",
    fontSize: scale(16),
    fontFamily: "SegoeUI",
    fontWeight: "400",
  },
});