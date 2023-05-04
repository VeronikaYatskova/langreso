/* eslint-disable eslint-comments/disable-enable-pair */
/* eslint-disable jsx-a11y/mouse-events-have-key-events */
/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable jsx-a11y/no-static-element-interactions */
import { Icon, Portal } from '@shared/ui'
import { PropsWithChildren, useRef, useState } from 'react'

import styles from './Question.module.scss'

export const QuestionFeature = ({ children }: PropsWithChildren) => {
	const [showInfo, change] = useState(false)
	const ref = useRef<HTMLDivElement | null>(null)

	return (
		<div ref={ref} className={styles.wrapper} onMouseMove={() => change(true)} onMouseOut={() => change(false)}>
			<div className={styles.btn}>Что это?</div>
			{showInfo && (
				<Portal>
					<div
						className={styles.info}
						style={{
							top: (ref.current?.offsetTop || 0) - 270 - (ref.current?.offsetHeight || 0),
							left: (ref.current?.offsetLeft || 0) - 270 - (ref.current?.offsetWidth || 0)
						}}
					>
						{children}
					</div>
				</Portal>
			)}
		</div>
	)
}
