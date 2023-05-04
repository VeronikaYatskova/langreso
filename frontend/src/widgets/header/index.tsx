/* eslint-disable eslint-comments/disable-enable-pair */
/* eslint-disable jsx-a11y/click-events-have-key-events */
/* eslint-disable jsx-a11y/no-static-element-interactions */
import { useState } from 'react'
import { Link } from 'react-router-dom'

import styles from './Header.module.scss'

import { appRoutes } from '@shared/config'
import { menuLinks } from '@widgets/menu/links'

export const Header = () => {

	return (
		<div className={styles.wrapper}>
			<Link to={appRoutes.base.goto()} className={styles.logo}>
				<h3>Home</h3>
			</Link>
			<div className={styles.links}>
				{menuLinks.map((menuLink, index) => (
							<Link to={menuLink.link} className={styles.link} key={index}>
								{menuLink.label}
							</Link>
						))}
			</div>
		</div>
	)
}
