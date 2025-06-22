import OnBoarding1 from "@/assets/svgs/onboarding1";
import OnBoarding2 from "@/assets/svgs/onboarding2";
import OnBoarding3 from "@/assets/svgs/onboarding3";

export const onBoardingData:onBoardingDataType[] = [
  {
    id: 1,
    title: "IT-SUP: Tư vấn sinh viên",
    subtitle: "Bạn là sinh viên khoa CNTT của trường ĐH SPKT? Bạn có thắc mắc muốn hỏi trực tuyến nhưng không tìm thấy ứng dụng hỗ trợ? Hãy thử ngay IT-Sup!",
    image: <OnBoarding1 />,
  },
  {
    id: 2,
    title: "IT-SUP: Hỗ trợ hết mình",
    subtitle: "Bạn đang ngại ngùng vì không dám đặt câu hỏi? IT-Sup hỗ trợ bạn hết mình mà không lưu lại bất kỳ dữ liệu hay đòi hỏi chi phí gì! Hãy thử ngay nhé!",
    image: <OnBoarding2 />,
  },
  {
    id: 3,
    title: "IT-SUP: Có hỗ trợ giọng nói",
    subtitle: "Hãy thử ngay và cho IT-Sup biết trải nghiệm của bạn nhé! Góp ý của bạn là động lực cho IT-Sup phát triển đó!",
    image: <OnBoarding3 />,
  },
];