import svgPaths from "./svg-x95y8v2itt";

function Group7() {
  return (
    <div className="absolute contents left-[21px] top-[12.5px]">
      <div className="absolute left-[21px] size-[162px] top-[12.5px]">
        <div className="absolute inset-[-7.407%]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 186 186">
            <g filter="url(#filter0_d_103_641)" id="Ellipse 19">
              <path d={svgPaths.p2e974800} fill="var(--fill-0, #EEEEEE)" />
            </g>
            <defs>
              <filter colorInterpolationFilters="sRGB" filterUnits="userSpaceOnUse" height="186" id="filter0_d_103_641" width="186" x="0" y="0">
                <feFlood floodOpacity="0" result="BackgroundImageFix" />
                <feColorMatrix in="SourceAlpha" result="hardAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" />
                <feMorphology in="SourceAlpha" operator="dilate" radius="12" result="effect1_dropShadow_103_641" />
                <feOffset />
                <feComposite in2="hardAlpha" operator="out" />
                <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.02 0" />
                <feBlend in2="BackgroundImageFix" mode="normal" result="effect1_dropShadow_103_641" />
                <feBlend in="SourceGraphic" in2="effect1_dropShadow_103_641" mode="normal" result="shape" />
              </filter>
            </defs>
          </svg>
        </div>
      </div>
      <div className="absolute left-[21px] size-[162px] top-[13.5px]">
        <div className="absolute bottom-0 left-0 right-[0.49%] top-[10.42%]">
          <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 162 146">
            <path d={svgPaths.pfadb200} fill="url(#paint0_linear_103_645)" id="Ellipse 18" />
            <defs>
              <linearGradient gradientUnits="userSpaceOnUse" id="paint0_linear_103_645" x1="0" x2="162" y1="65" y2="65">
                <stop stopColor="#FF8008" />
                <stop offset="1" stopColor="#FFC837" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>
      <p className="absolute font-['Roboto:Bold',_sans-serif] font-bold leading-[normal] left-[80px] text-[25px] text-black text-nowrap top-[79.5px] whitespace-pre" style={{ fontVariationSettings: "'wdth' 100" }}>
        70%
      </p>
    </div>
  );
}

function ChartGraphic() {
  return (
    <div className="h-[189px] overflow-clip relative shrink-0 w-[204px]" data-name="chart-graphic">
      <Group7 />
    </div>
  );
}

function CardBody() {
  return (
    <div className="relative shrink-0 w-full" data-name="card-body">
      <div className="flex flex-col items-center justify-center overflow-clip rounded-[inherit] size-full">
        <div className="box-border content-stretch flex flex-col gap-[15px] items-center justify-center px-[86px] py-[25px] relative w-full">
          <ChartGraphic />
        </div>
      </div>
    </div>
  );
}

export default function Card() {
  return (
    <div className="bg-white content-stretch flex flex-col items-center justify-between overflow-clip relative rounded-[20px] size-full" data-name="card">
      <CardBody />
    </div>
  );
}